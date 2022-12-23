# Copyright (c) 2022 Genome Research Ltd.
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
# this program. If not, see <http://www.gnu.org/licenses/>.

from typing import List

from ml_warehouse.schema import PacBioRunWellMetrics
from pydantic import Extra, Field
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from lang_qc.db.qc_schema import QcState, QcStateDict, QcType
from lang_qc.models.pacbio.well import PacBioPagedWells, PacBioWell
from lang_qc.models.pager import PagedStatusResponse
from lang_qc.models.qc_flow_status import QcFlowStatusEnum
from lang_qc.models.qc_state import QcState as QcStateModel

FILTERS = {
    QcFlowStatusEnum.ON_HOLD.name: (QcStateDict.state == "On hold"),
    QcFlowStatusEnum.QC_COMPLETE.name: (QcState.is_preliminary == 0),
    QcFlowStatusEnum.IN_PROGRESS.name: and_(
        QcState.is_preliminary == 1, QcStateDict.state != "On hold"
    ),
}


class PacBioPagedWellsFactory(PagedStatusResponse):
    """
    Factory class to create `PacBioPagedWells` objects that correspond to
    the criteria given by the attributes of the object, i.e. `page_size`
    `page_number` and `qc_flow_status` attributes.
    """

    qcdb_session: Session = Field(
        title="SQLAlchemy Session",
        description="A SQLAlchemy Session for the LangQC database",
    )
    mlwh_session: Session = Field(
        title="SQLAlchemy Session",
        description="A SQLAlchemy Session for the ml warehouse database",
    )

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.forbid

    def wells2paged_wells(self, wells: List[PacBioWell]) -> PacBioPagedWells:
        """
        Given a list of `PacBioWell` objects, slices the list according to the
        value of the `page_size` and `page_number` attributes and returns a
        corresponding `PacBioPagedWells` object.

        Legacy method, will be removed as soon as the `create` method can handle
        requests for teh inbox wells
        """
        return PacBioPagedWells(
            page_number=self.page_number,
            page_size=self.page_size,
            total_number_of_items=len(wells),
            qc_flow_status=self.qc_flow_status,
            wells=self.slice_data(wells),
        )

    def create(self) -> PacBioPagedWells:
        """
        Returns `PacBioPagedWells` object that corresponds to the criteria
        specified by the `page_size`, `page_number, and `qc_flow_status`
        attributes.

        The `PacBioWell` objects in `wells` attribute of the returned object
        are sorted in a way appropriate for the requested `qc_flow_status`.
        For non-inbox requests the wells with most recently assigned QC states
        come first.

        The inbox requests are not yet implemented.
        """

        if self.qc_flow_status == QcFlowStatusEnum.INBOX:
            raise Exception("Not implemented")

        wells = self._get_wells()
        # self._add_tracking_info(wells)

        return PacBioPagedWells(
            page_number=self.page_number,
            page_size=self.page_size,
            total_number_of_items=self.total_number_of_items,
            qc_flow_status=self.qc_flow_status,
            wells=wells,
        )

    def _build_query4status(self):

        # TODO: add filtering by the seq platform

        # Build the common part of the query.
        # Sort by the date the current QC state was assigned, latest first.
        query = (
            select(QcState)
            .join(QcType)
            .join(QcStateDict)
            .where(QcType.qc_type == "sequencing")
            .order_by(QcState.date_updated.desc())
        )
        # Add status-specific part of the query.
        return query.where(FILTERS[self.qc_flow_status.name])

    def _retrieve_qc_states(self):

        states = self.qcdb_session.execute(self._build_query4status()).scalars().all()
        # Save the number of retrieved rows - needed to page correctly and here
        #  and needed by the client to correctly set up the paging widget.
        self.total_number_of_items = len(states)
        # Return the states for the wells we were asked to fetch, max - page_size, min - 0.

        return self.slice_data(states)

    def _get_wells(self) -> List[PacBioWell]:

        # Note that the run name and well label are sourced from the QC database.
        # They'd better be correct there!
        wells = []
        for qc_state in self._retrieve_qc_states():
            sub_product = qc_state.seq_product.product_layout[0].sub_product
            # TODO: consider adding from_orm method to PacBioWell
            wells.append(
                PacBioWell(
                    run_name=sub_product.value_attr_one,
                    label=sub_product.value_attr_two,
                    qc_state=QcStateModel.from_orm(qc_state),
                )
            )
        return wells

    def _add_tracking_info(self, wells: List[PacBioWell]):

        # Will use the run name and well label to retrieve relevant rows from mlwh.
        # In future, when available in mlwh for all records, product IDs can be used.

        for well in wells:
            # One query for all or query per well? The latter for now to avoid the need
            # to match the records later. Should be fast enough for small-ish pages, we
            # query on a unique key.
            db_well = self.mlwh_session.execute(
                select(PacBioRunWellMetrics).where(
                    and_(
                        PacBioRunWellMetrics.pac_bio_run_name == well.run_name,
                        PacBioRunWellMetrics.well_label == well.label,
                    )
                )
            ).scalars.one_or_none()
            # No error if no matching mlwh record is found.
            # TODO: log a warning.
            if db_well is not None:
                well.run_start_time = db_well.run_start
                well.run_complete_time = db_well.run_complete
                well.well_start_time = db_well.well_start
                well.well_complete_time = db_well.well_complete
