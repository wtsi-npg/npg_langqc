# Copyright (c) 2022, 2023, 2024 Genome Research Ltd.
#
# Authors:
#   Marina Gourtovaia <mg8@sanger.ac.uk>
#   Kieron Taylor <kt19@sanger.ac.uk>
#
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

from statistics import mean, stdev
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.dataclasses import dataclass

from lang_qc.db.mlwh_schema import PacBioRunWellMetrics
from lang_qc.util.errors import MissingLimsDataError
from lang_qc.util.type_checksum import PacBioProductSHA256


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


def movie_minutes(obj, key):
    "Convert to hours"
    return round(getattr(obj, key) / 60)


def percentage_reads(obj, key):
    if getattr(obj, key) == 0:
        return 0
    if (divisor := sum_of_productive_reads(obj)) != 0:
        return round((getattr(obj, key) / divisor) * 100, 2)
    return None


def convert_to_gigabase(obj, key):
    return round(getattr(obj, key) / 1000000000, 2)


def rounding(obj, key):
    return round(getattr(obj, key), 2)


def demux_reads(obj, _):
    if getattr(obj, "demultiplex_mode") == "OnInstrument":
        return round(
            getattr(obj, "hifi_barcoded_reads") / getattr(obj, "hifi_num_reads") * 100,
            2,
        )
    return None


def demux_bases(obj, _):
    if getattr(obj, "demultiplex_mode") == "OnInstrument":
        return round(
            getattr(obj, "hifi_bases_in_barcoded_reads")
            / getattr(obj, "hifi_read_bases")
            * 100,
            2,
        )
    return None


dispatch = {
    "movie_minutes": (movie_minutes, ["movie_minutes"]),
    "p0_num": (percentage_reads, ["p0_num", "p1_num", "p2_num"]),
    "p1_num": (percentage_reads, ["p0_num", "p1_num", "p2_num"]),
    "p2_num": (percentage_reads, ["p0_num", "p1_num", "p2_num"]),
    "hifi_read_bases": (convert_to_gigabase, ["hifi_read_bases"]),
    "polymerase_read_bases": (convert_to_gigabase, ["polymerase_read_bases"]),
    "local_base_rate": (rounding, ["local_base_rate"]),
    "percentage_deplexed_reads": (
        demux_reads,
        ["hifi_barcoded_reads", "hifi_num_reads"],
    ),
    "percentage_deplexed_bases": (
        demux_bases,
        ["hifi_bases_in_barcoded_reads", "hifi_read_bases"],
    ),
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
    loading_conc: dict = Field(default=None, title="Loading concentration (pM)")
    p0_num: dict = Field(default=None, title="P0 %")
    p1_num: dict = Field(default=None, title="P1 %")
    p2_num: dict = Field(default=None, title="P2 %")
    polymerase_read_bases: dict = Field(default=None, title="Total Cell Yield (Gb)")
    polymerase_read_length_mean: dict = Field(
        default=None, title="Mean Polymerase Read Length (bp)"
    )
    movie_minutes: dict = Field(default=None, title="Run Time (hr)")
    percentage_deplexed_reads: dict = Field(
        default=None, title="Percentage of reads deplexed"
    )
    percentage_deplexed_bases: dict = Field(
        default=None, title="Percentage of bases deplexed"
    )
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: PacBioRunWellMetrics):

        # Introspect the class definition, get a dictionary of specs
        # for properties with property names as the keys.
        attrs = cls.model_json_schema()["properties"]
        qc_data = {}

        for name in attrs:
            if name == "smrt_link":
                # This one is special
                qc_data[name] = get_ids_for_smrtlink_url(obj)
            else:
                qc_data[name] = {}
                qc_data[name]["value"] = None
                qc_data[name]["label"] = attrs[name]["title"]

                if name in dispatch:
                    callable, obj_keys = dispatch[name]
                    # Check all keys required for dispatch have values
                    if all(getattr(obj, key, None) for key in obj_keys):
                        qc_data[name]["value"] = callable(obj, name)
                else:
                    qc_data[name]["value"] = getattr(obj, name, None)

        return cls.model_validate(qc_data)


class SampleDeplexingStats(BaseModel):
    """
    A representation of metrics for one product, some direct from the DB and others inferred

    For a long time tag2_name was null and tag1_name was silently used at both ends of the sequence.
    As a result tag2_name will be None for most data in or before 2024.
    """

    id_product: PacBioProductSHA256
    tag1_name: str | None
    tag2_name: str | None
    deplexing_barcode: str | None
    hifi_read_bases: float | None = Field(title="HiFi read bases (Gb)")
    hifi_num_reads: int | None
    hifi_read_length_mean: float | None
    hifi_bases_percent: float | None
    percentage_total_reads: float | None


@dataclass(kw_only=True, frozen=True)
class QCPoolMetrics:

    db_well: PacBioRunWellMetrics = Field(init_var=True)
    pool_coeff_of_variance: float | None = Field(
        title="Coefficient of variance for reads in the pool",
        description="Percentage of the standard deviation w.r.t. mean, when pool is more than one",
    )
    products: list[SampleDeplexingStats] = Field(
        title="List of products and their metrics"
    )

    @model_validator(mode="before")
    def pre_root(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Populates this object with the run and well tracking information
        from a database row that is passed as an argument.
        """

        db_well_key_name = "db_well"
        # https://github.com/pydantic/pydantic-core/blob/main/python/pydantic_core/_pydantic_core.pyi
        if db_well_key_name not in values.kwargs:
            return values.kwargs

        well: PacBioRunWellMetrics = values.kwargs[db_well_key_name]
        if well is None:
            raise ValueError(f"None {db_well_key_name} value is not allowed.")

        cov: float | None = None
        sample_stats = []

        if well.demultiplex_mode and "Instrument" in well.demultiplex_mode:
            product_metrics = well.pac_bio_product_metrics
            lib_lims_data = [
                product.pac_bio_run
                for product in product_metrics
                if product.pac_bio_run is not None
            ]
            if len(lib_lims_data) != len(product_metrics):
                raise MissingLimsDataError(
                    "Partially linked LIMS data or no linked LIMS data"
                )

            if any(p.hifi_num_reads is None for p in product_metrics):
                cov = None
            else:
                hifi_reads = [prod.hifi_num_reads for prod in product_metrics]
                if len(hifi_reads) > 1:
                    # stdev throws on n=1
                    cov = round(stdev(hifi_reads) / mean(hifi_reads) * 100, 2)

            for i, prod in enumerate(product_metrics):
                sample_stats.append(
                    SampleDeplexingStats(
                        id_product=prod.id_pac_bio_product,
                        tag1_name=lib_lims_data[i].tag_identifier,
                        tag2_name=lib_lims_data[i].tag2_identifier,
                        deplexing_barcode=prod.barcode4deplexing,
                        hifi_read_bases=convert_to_gigabase(prod, "hifi_read_bases"),
                        hifi_num_reads=prod.hifi_num_reads,
                        hifi_read_length_mean=prod.hifi_read_length_mean,
                        hifi_bases_percent=prod.hifi_bases_percent,
                        percentage_total_reads=(
                            round(prod.hifi_num_reads / well.hifi_num_reads * 100, 2)
                            if (well.hifi_num_reads and prod.hifi_num_reads)
                            else None
                        ),
                    )
                )

        return {"pool_coeff_of_variance": cov, "products": sample_stats}
