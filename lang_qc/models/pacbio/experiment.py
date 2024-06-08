# Copyright (c) 2023, 2024 Genome Research Ltd.
#
# Authors:
#   Marina Gourtovaia <mg8@sanger.ac.uk>
#   Kieron Taylor <kt19@sanger.ac.uk>
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
# this program. If not, see <http://www.gnu.org/licenses/>.

from typing import Any

from pydantic import Field, model_validator
from pydantic.dataclasses import dataclass

from lang_qc.db.mlwh_schema import PacBioRun


@dataclass(kw_only=True, frozen=True)
class PacBioLibrary:
    """
    This model represents LIMS data associated with a PacBio library.

    The fields of the model can be assigned directly via the constructor.
    However, if the `db_library` field, a single row of the PacBioRun table
    class, is set via the constructor, the rest of the fields are populated
    using this database row object, while  any other information passed to the
    constructor is disregarded.

    The  `db_library` field is not present in the model instance that is
    returned by the constructor.
    """

    db_library: PacBioRun = Field(init_var=True)

    study_id: str = Field(
        title="LIMS-specific study identifier",
    )
    study_name: str = Field(
        title="Study name",
    )
    sample_id: str = Field(
        title="LIMS-specific Sample identifier",
    )
    sample_name: str = Field(
        title="Sample name",
    )
    tag_sequence: list = Field(
        title="Tag sequence",
        description="""
        Tag sequences as a list. An empty list for a non-indexed library.
        """,
    )
    library_type: str | None = Field(
        default=None,
        title="Library type",
    )
    pool_name: str | None = Field(
        default=None,
        title="Pool name",
        description="""
        The pac_bio_library_tube_barcode from TRACTION, AKA pool name
        """,
    )

    @model_validator(mode="before")
    def pre_root(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Populates the fields of this object with information available
        in the LIMS system. Errors if the `db_library` attribute is not
        set via the constructor.
        """

        # https://github.com/pydantic/pydantic-core/blob/main/python/pydantic_core/_pydantic_core.pyi
        if "db_library" not in values.kwargs:
            return values.kwargs
        db_row: PacBioRun = values.kwargs["db_library"]
        if db_row is None:
            raise ValueError("None db_library value is not allowed.")

        assigned = dict()
        study = db_row.study
        assigned["study_name"] = study.name
        assigned["study_id"] = study.id_study_lims
        sample = db_row.sample
        assigned["sample_name"] = sample.name
        assigned["sample_id"] = sample.id_sample_lims
        assigned["library_type"] = db_row.pipeline_id_lims
        assigned["pool_name"] = db_row.pac_bio_library_tube_barcode
        assigned["tag_sequence"] = []
        if tag := db_row.tag_sequence:
            assigned["tag_sequence"].append(tag)
            if tag := db_row.tag2_sequence:
                assigned["tag_sequence"].append(tag)

        return assigned


@dataclass(kw_only=True, frozen=True)
class PacBioExperiment:
    """
    A response model that contains laboratory tracking information
    about the PacBio wells and samples prior to the start of the
    sequencing run. The current source of the information is the
    multi-lims warehouse.

    The model is capable of representing both a well with either a
    single sample or multiple samples and a single sample (library).

    The class is agnostic to the nature of the entity it represents.
    It gives a reasonable representation of data for a multi-sample
    well. Data for a well can also be modelled as a list of
    PacBioExperiment objects, each object representing a single sample
    (library).
    """

    db_libraries: list[PacBioRun] = Field(init_var=True)

    study_id: list = Field(
        title="Study identifier",
        description="""
        Study identifiers as a sorted list of unique strings (to cover
        an unlikely case of multiple studies).
        """,
    )
    study_name: str | None = Field(
        default=None,
        title="Study name",
        description="""
        Study name, is not set in case of multiple studies.
        """,
    )
    sample_id: str | None = Field(
        default=None,
        title="Sample identifier",
        description="""
        Sample identifier, is not set in case of multiple samples.
        """,
    )
    sample_name: str | None = Field(
        default=None,
        title="Sample name",
        description="""
        Sample name, is not set in case of multiple samples.
        """,
    )
    num_samples: int = Field(
        default=1,
        title="Number of samples",
        description="""
        Number of samples. If the data is for a well, multiple
        samples might be present.
        """,
    )
    tag_sequence: list = Field(
        title="Tag sequence",
        description="""
        Tag sequences as a list. The list is empty in case of multiple
        samples or if the library for the only present sample does not
        have the index sequence.
        """,
    )
    library_type: list = Field(
        title="Library type",
        description="""
        Library types as a sorted list of unique strings to cover an
        unlikely case of multiple library types.
        """,
    )
    pool_name: str | None = Field(
        default=None,
        title="Pool name",
        description="""
        The pac_bio_library_tube_barcode from TRACTION, AKA pool name
        """,
    )

    @model_validator(mode="before")
    def pre_root(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Populates the fields of this object with information available
        in the LIMS system.
        Errors if the `db_libraries` attribute is not set via the constructor.
        """

        lims_db_rows: list[PacBioRun] = values.kwargs["db_libraries"]
        num_samples = len(lims_db_rows)
        if num_samples == 0:
            raise ValueError("Empty db_libraries list is not allowed.")

        lib_objects = [PacBioLibrary(db_library=row) for row in lims_db_rows]

        lims_data = {
            "num_samples": num_samples,
            "tag_sequence": [],
        }

        lims_data["study_id"] = {o.study_id for o in lib_objects}  # returns a set
        lims_data["library_type"] = {
            o.library_type if o.library_type is not None else "UNKNOWN"
            for o in lib_objects
        }

        pool_names = {o.pool_name for o in lib_objects}
        if len(pool_names) > 1:
            raise ValueError("Multiple pool names.")
        lims_data["pool_name"] = pool_names.pop()

        o = lib_objects[0]
        if num_samples == 1:
            lims_data["tag_sequence"] = o.tag_sequence
            lims_data["sample_id"] = o.sample_id
            lims_data["sample_name"] = o.sample_name
            lims_data["study_name"] = o.study_name
        if len(lims_data["study_id"]) == 1:
            lims_data["study_name"] = o.study_name

        # Convert sets back to lists and sort so that the items are
        # in a predictable order.
        for key in ("library_type", "study_id"):
            lims_data[key] = sorted(lims_data[key])

        return lims_data
