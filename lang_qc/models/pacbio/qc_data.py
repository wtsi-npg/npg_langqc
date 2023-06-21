# Copyright (c) 2022, 2023 Genome Research Ltd.
#
# Author: Marina Gourtovaia <mg8@sanger.ac.uk>
#
# This file is part of npg_langqc.
#
# npg_langqc is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>

from pydantic import BaseModel, Field

from lang_qc.db.mlwh_schema import PacBioRunWellMetrics

# Pydantic prohibits us from defining these as @classmethod or @staticmethod
# Lots of self deliberately overlooked
def get_ids_for_smrtlink_url(obj):
    return {
        "run_uuid": obj.sl_run_uuid,
        "dataset_uuid": obj.sl_ccs_uuid,
        "hostname": obj.sl_hostname,
    }

def sum_of_productive_reads(obj):
    return (obj.p0_num or 0) + (obj.p1_num or 0) + (obj.p2_num or 0)

def value_ise(value):
    return {"value": value}

def movie_minutes(obj, key):
    return value_ise(round(getattr(obj, key) / 60))

def percentage_reads(obj, key):
    if getattr(obj, key) == 0:
        return value_ise(0)

    divisor = sum_of_productive_reads(obj)
    if divisor != 0:
        return value_ise(round((getattr(obj, key) / divisor) * 100, 2))
    return None

def convert_to_gigabase(obj, key):
    return value_ise(round(getattr(obj, key) / 1000000000, 2))

def rounding(obj, key):
    return value_ise(round(getattr(obj, key), 2))


dispatch = {
    "movie_minutes": movie_minutes,
    "p0_num": percentage_reads,
    "p1_num": percentage_reads,
    "p2_num": percentage_reads,
    "hifi_read_bases": convert_to_gigabase,
    "polymerase_read_bases": convert_to_gigabase,
    "local_base_rate": rounding
}


class QCDataWell(BaseModel):

    smrt_link: dict = Field(title="URL components for a SMRT Link page")
    binding_kit: dict = Field(default=None, title="Binding Kit")
    control_num_reads: dict = Field(default=None, title="Number of Control Reads")
    control_read_length_mean: dict = Field(
        default=None, title="Control Read Length (bp)"
    )
    hifi_read_bases: dict = Field(default=None, title="CCS Yield (Gb)")
    hifi_read_length_mean: dict = Field(default=None, title="CCS Mean Length (bp)")
    local_base_rate: dict = Field(default=None, title="Local Base Rate")
    p0_num: dict = Field(default=None, title="P0 %")
    p1_num: dict = Field(default=None, title="P1 %")
    p2_num: dict = Field(default=None, title="P2 %")
    polymerase_read_bases: dict = Field(default=None, title="Total Cell Yield (Gb)")
    polymerase_read_length_mean: dict = Field(
        default=None, title="Mean Polymerase Read Length (bp)"
    )
    movie_minutes: dict = Field(default=None, title="Run Time (hr)")

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: PacBioRunWellMetrics):

        # Introspect the class definition, get a dictionary of specs
        # for properties with property names as the keys.
        attrs = cls.schema()["properties"]
        qc_data = {}

        for name in attrs:
            if (name == "smrt_link"):
                # This one is special
                qc_data[name] = get_ids_for_smrtlink_url(obj)
            else:
                qc_data[name] = {}

                if name in dispatch and getattr(obj, name, None):
                    qc_data[name] = dispatch[name](obj, name)
                else:
                    qc_data[name]["value"] = getattr(obj, name, None)

                # Add label to each item
                qc_data[name]["label"] = attrs[name]["title"]

        return cls.parse_obj(qc_data)
