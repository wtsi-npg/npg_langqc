# Copyright (c) 2023 Genome Research Ltd.
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

from typing import List

from pydantic import BaseModel, ConfigDict, Field

from lang_qc.db.mlwh_schema import PacBioRun


class PacBioExperiment(BaseModel):
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

    study_id: list = Field(
        title="Study identifier",
        description="""
        Study identifiers as a sorted list of unique strings (to cover
        an unlikely case of multiple studies).
        """,
    )
    study_name: str = Field(
        default=None,
        title="Study name",
        description="""
        Study name, is not set in case of multiple studies.
        """,
    )
    sample_id: str = Field(
        default=None,
        title="Sample identifier",
        description="""
        Sample identifier, is not set in case of multiple samples.
        """,
    )
    sample_name: str = Field(
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
    pool_name: str = Field(
        default=None,
        title="Pool name",
        description="""
        The pac_bio_library_tube_barcode from TRACTION, AKA pool name
        """,
    )
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @classmethod
    def from_orm(cls, lims_db_rows: List[PacBioRun]):
        """
        A factory method, creates an instance of the PacBioLimsData class.
        Should be given a non-empty list of PacBioRun table row objects as
        an argument.
        """

        num_samples = len(lims_db_rows)
        if num_samples == 0:
            raise Exception("Cannot create PacBioLimsData object, no data.")
        if any(row is None for row in lims_db_rows):
            raise Exception("Cannot create PacBioLimsData object, None row.")

        # Using sets for some data instead of lists because we do not
        # want repetitions.
        lims_data = {
            "num_samples": num_samples,
            "study_id": set(),
            "library_type": set(),
            "tag_sequence": [],
        }
        study_name = None
        for row in lims_db_rows:
            lims_data["study_id"].add(row.study.id_study_lims)
            lims_data["library_type"].add(row.pipeline_id_lims)
            study_name = row.study.name
            if pool_name := row.pac_bio_library_tube_barcode:
                lims_data["pool_name"] = pool_name
            if num_samples == 1:
                if tag := row.tag_sequence:
                    lims_data["tag_sequence"].append(tag)
                    if tag := row.tag2_sequence:
                        lims_data["tag_sequence"].append(tag)
                lims_data["sample_id"] = row.sample.id_sample_lims
                lims_data["sample_name"] = row.sample.name
                lims_data["study_name"] = row.study.name

        if len(lims_data["study_id"]) == 1:
            lims_data["study_name"] = study_name

        # Convert sets back to lists and sort so that the list items are
        # in a predictable order.
        for key in ("library_type", "study_id"):
            lims_data[key] = sorted(lims_data[key])

        return cls.model_validate(lims_data)
