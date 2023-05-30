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

        straight_map_attr_names = {
            "binding_kit",
            "control_num_reads",
            "control_read_length_mean",
            "hifi_read_length_mean",
            "local_base_rate",
            "polymerase_read_length_mean",
        }

        qc_data = {}

        sum_of_productive_reads = (
            (obj.p0_num or 0) + (obj.p1_num or 0) + (obj.p2_num or 0)
        )

        for name in attrs:

            if name == "smrt_link":
                qc_data[name] = {
                    "run_uuid": obj.sl_run_uuid,
                    "dataset_uuid": obj.sl_ccs_uuid,
                    "hostname": obj.sl_hostname,
                }
                continue

            value = getattr(obj, name)

            if (value is not None) and (name not in straight_map_attr_names):
                if name == "movie_minutes":
                    value = round(value / 60)
                elif name in ["p0_num", "p1_num", "p2_num"]:
                    if value == 0:
                        # We retain zero value whatever the denominator is.
                        pass
                    else:
                        if sum_of_productive_reads != 0:
                            value = (value / sum_of_productive_reads) * 100
                        else:
                            value = None
                else:
                    value = value / 1000000000

            if isinstance(value, float):
                value = round(value, 2)

            # Label is the value of the title of the property
            # as defined in this class in the code above.
            qc_data[name] = {"value": value, "label": attrs[name]["title"]}

        return cls.parse_obj(qc_data)
