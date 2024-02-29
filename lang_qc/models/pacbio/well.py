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

from pydantic import ConfigDict, Field
from dataclasses import dataclass, InitVar, field
from sqlalchemy.orm import Session

from lang_qc.db.helper.qc import get_qc_states_by_id_product_list
from lang_qc.db.mlwh_schema import PacBioRunWellMetrics
from lang_qc.models.pacbio.experiment import PacBioExperiment
from lang_qc.models.pacbio.qc_data import QCDataWell
from lang_qc.models.pager import PagedResponse
from lang_qc.models.qc_state import QcState


@dataclass
class PacBioWell:

    db_well: InitVar[PacBioRunWellMetrics]
    

    """
    A response model for a single PacBio well on a particular PacBio run.
    The class contains the attributes that uniquely define this well (`run_name`
    and `label`), along with the time line and the current QC state of this well,
    if any.

    This model does not contain any information about data that was
    sequenced or QC metrics or assessment for such data.
    """

    # Well identifies.
    id_product: str = field(init=False, default=None)
    label: str = field(init=False, default=None)
    plate_number: Optional[int] = field(init=False, default=None)
    run_name: str = field(init=False, default=None)

    qc_session: InitVar[Session | None] = None

    # Run and well tracking information from SMRT Link
    run_start_time: datetime | None = field(default=None, init=False)
    run_complete_time: datetime | None = field(default=None, init=False)
    well_start_time: datetime | None = field(default=None, init=False)
    well_complete_time: datetime | None = field(default=None, init=False)
    run_status: str = field(default=None, init=False)
    well_status: str = field(default=None, init=False)
    instrument_name: str = field(default=None, init=False)
    instrument_type: str = field(default=None, init=False)

    qc_state: QcState = field(default=None)

    def __post_init__(self, db_well):
        """
        Populates this object with the run and well tracking information
        from a database row that is passed as an argument.
        """
        self.id_product = db_well.id_pac_bio_product
        self.label = db_well.well_label
        self.plane_number = db_well.plate_number
        self.run_name = db_well.pac_bio_run_name
        self.run_start_time = db_well.run_start
        self.run_complete_time = db_well.run_complete
        self.well_start_time = db_well.well_start
        self.well_complete_time = db_well.well_complete
        self.run_status = db_well.run_status
        self.well_status = db_well.well_status
        self.instrument_name = db_well.instrument_name
        self.instrument_type = db_well.instrument_type

        return self


class PacBioPagedWells(PagedResponse, extra="forbid"):
    """
    A response model for paged data about PacBio wells.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    wells: list[PacBioWell] = Field(
        default=[],
        title="A list of PacBioWell objects",
        description="""
        A list of `PacBioWell` objects that corresponds to the page number
        and size specified by the `page_size` and `page_number` attributes.
        """,
    )

@dataclass
class PacBioWellFull(PacBioWell):
    """
    A response model for a single PacBio well on a particular PacBio run.
    The class contains the attributes that uniquely define this well (`run_name`
    and `label`), along with the laboratory experiment and sequence run tracking
    information, current QC state of this well and QC data for this well.
    """

    metrics: QCDataWell = field(init=False)
    experiment_tracking: PacBioExperiment = field(default=None, init=False)
    

    def __post_init__(self, db_well, qc_session):

        super().__post_init__(db_well)
    
        self.metrics = (QCDataWell.from_orm(db_well),)
        experiment_info = []
        for row in db_well.pac_bio_product_metrics:
            exp_row = row.pac_bio_run
            if exp_row:
                experiment_info.append(exp_row)
            else:
                # Do not supply incomplete data.
                experiment_info = []
                break
        if len(experiment_info):
            self.experiment_tracking = PacBioExperiment.from_orm(experiment_info)
        qced_products = get_qc_states_by_id_product_list(
            session=qc_session, ids=[self.id_product], sequencing_outcomes_only=True
        ).get(self.id_product)
        if qced_products is not None:
            self.qc_state = qced_products[0]

        return self
