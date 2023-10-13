# Copyright (c) 2022, 2023 Genome Research Ltd.
#
# Authors:
#  Adam Blanchet
#  Marina Gourtovaia <mg8@sanger.ac.uk>
#  Kieron Taylor <kt19@sanger.ac.uk>
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

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from lang_qc.db.helper.qc import get_qc_states_by_id_product_list
from lang_qc.db.mlwh_schema import PacBioRunWellMetrics
from lang_qc.models.pacbio.experiment import PacBioExperiment
from lang_qc.models.pacbio.qc_data import QCDataWell
from lang_qc.models.pager import PagedResponse
from lang_qc.models.qc_state import QcState


class PacBioWell(BaseModel, extra="forbid"):
    """
    A response model for a single PacBio well on a particular PacBio run.
    The class contains the attributes that uniquely define this well (`run_name`
    and `label`), along with the time line and the current QC state of this well,
    if any.

    This model does not contain any information about data that was
    sequenced or QC metrics or assessment for such data.
    """

    # Well identifies.
    id_product: str = Field(title="Product identifier")
    label: str = Field(title="Well label", description="The label of the PacBio well")
    plate_number: Optional[int] = Field(
        default=None,
        title="Plate number",
        description="Plate number, relevant for Revio instruments only",
    )
    run_name: str = Field(
        title="Run name", description="PacBio run name as registered in LIMS"
    )
    # Run and well tracking information from SMRT Link
    run_start_time: datetime = Field(default=None, title="Run start time")
    run_complete_time: datetime = Field(default=None, title="Run complete time")
    well_start_time: datetime = Field(default=None, title="Well start time")
    well_complete_time: datetime = Field(default=None, title="Well complete time")
    run_status: str = Field(default=None, title="Current PacBio run status")
    well_status: str = Field(default=None, title="Current PacBio well status")
    instrument_name: str = Field(default=None, title="Instrument name")
    instrument_type: str = Field(default=None, title="Instrument type")

    qc_state: QcState = Field(
        default=None,
        title="Current QC state of this well",
        description="""
        Current QC state of this well as a QcState pydantic model.
        The well might have no QC state assigned. Whether the QC state is
        available depends on the lifecycle stage of this well.
        """,
    )

    def copy_run_tracking_info(self, db_well: PacBioRunWellMetrics):
        """
        Populates this object with the run and well tracking information
        from a database row that is passed as an argument.
        """
        self.run_start_time = db_well.run_start
        self.run_complete_time = db_well.run_complete
        self.well_start_time = db_well.well_start
        self.well_complete_time = db_well.well_complete
        self.run_status = db_well.run_status
        self.well_status = db_well.well_status
        self.instrument_name = db_well.instrument_name
        self.instrument_type = db_well.instrument_type


class PacBioPagedWells(PagedResponse, extra="forbid"):
    """
    A response model for paged data about PacBio wells.
    """

    wells: list[PacBioWell] = Field(
        default=[],
        title="A list of PacBioWell objects",
        description="""
        A list of `PacBioWell` objects that corresponds to the page number
        and size specified by the `page_size` and `page_number` attributes.
        """,
    )


class PacBioWellFull(PacBioWell):
    """
    A response model for a single PacBio well on a particular PacBio run.
    The class contains the attributes that uniquely define this well (`run_name`
    and `label`), along with the laboratory experiment and sequence run tracking
    information, current QC state of this well and QC data for this well.
    """

    metrics: QCDataWell = Field(
        title="Currently available QC data for well",
    )
    experiment_tracking: PacBioExperiment = Field(
        default=None,
        title="Experiment tracking information",
        description="""
        Laboratory experiment tracking information for this well, if available.
        """,
    )
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @classmethod
    def from_orm(cls, mlwh_db_row: PacBioRunWellMetrics, qc_session: Session):

        id_product = mlwh_db_row.id_pac_bio_product
        obj = cls(
            id_product=id_product,
            run_name=mlwh_db_row.pac_bio_run_name,
            plate_number=mlwh_db_row.plate_number,
            label=mlwh_db_row.well_label,
            metrics=QCDataWell.from_orm(mlwh_db_row),
        )
        obj.copy_run_tracking_info(mlwh_db_row)

        experiment_info = []
        for row in mlwh_db_row.pac_bio_product_metrics:
            exp_row = row.pac_bio_run
            if exp_row:
                experiment_info.append(exp_row)
            else:
                # Do not supply incomplete data.
                experiment_info = []
                break
        if len(experiment_info):
            obj.experiment_tracking = PacBioExperiment.from_orm(experiment_info)

        qced_products = get_qc_states_by_id_product_list(
            session=qc_session, ids=[id_product], sequencing_outcomes_only=True
        ).get(id_product)
        if qced_products is not None:
            obj.qc_state = qced_products[0]

        return obj
