# Copyright (c) 2022, 2023 Genome Research Ltd.
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

import logging
from datetime import date, datetime, timedelta
from typing import ClassVar, List

from ml_warehouse.schema import PacBioRunWellMetrics
from pydantic import BaseModel, Extra, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from lang_qc.db.helper.well import WellQc
from lang_qc.db.qc_schema import QcState, QcStateDict, QcType
from lang_qc.models.pacbio.well import PacBioPagedWells, PacBioWell
from lang_qc.models.pager import PagedStatusResponse
from lang_qc.models.qc_flow_status import QcFlowStatusEnum
from lang_qc.models.qc_state import QcState as QcStateModel

"""
This package is using an undocumented feature of Pydantic, type
`ClassVar`, which was introduced in https://github.com/pydantic/pydantic/pull/339
Here this type is used to mark a purely internal to the class variables.
"""


class WellWh(BaseModel):
    """
    A data access class for routine SQLAlchemy operations on wells data
    in ml warehouse database.
    """

    session: Session = Field(
        title="SQLAlchemy Session",
        description="A SQLAlchemy Session for the ml warehouse database",
    )
    INBOX_LOOK_BACK_NUM_WEEKS: ClassVar = 4

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True

    def get_well(self, run_name: str, well_label: str) -> PacBioRunWellMetrics | None:
        """
        Returns a well row record from the well metrics table or
        None if the record does not exist.
        """

        return self.session.execute(
            select(PacBioRunWellMetrics).where(
                and_(
                    PacBioRunWellMetrics.pac_bio_run_name == run_name,
                    PacBioRunWellMetrics.well_label == well_label,
                )
            )
        ).scalar_one_or_none()

    def well_exists(self, run_name: str, well_label: str) -> bool:
        """
        Returns `True` if a record for combination of a well and a run exists,
        in the well metrics table `False` otherwise.
        """

        return bool(self.get_well(run_name, well_label))

    def recent_completed_wells(self) -> List[PacBioRunWellMetrics]:
        """
        Get recent completed wells from the mlwh database.
        The implementation of the inbox query might change when the QC outcomes
        become available in mlwh.
        """

        ######
        # It is important not to show aborted wells in the inbox.
        #
        # The well can be complete as in Illumina 'run complete' but that's not
        # the same as analysis complete which the other conditions are trying for.
        # It potentially gets a bit easier with v11 but those conditions should
        # still work ok.
        #

        # Using current local time.
        # Generating a date rather than a timestamp here in order to have a consistent
        # earliest date for the look-back period during the QC team's working day.
        my_date = date.today() - timedelta(weeks=self.INBOX_LOOK_BACK_NUM_WEEKS)
        look_back_min_date = datetime(my_date.year, my_date.month, my_date.day)

        # TODO: fall back to run_complete when well_complete is undefined

        query = (
            select(PacBioRunWellMetrics)
            .where(PacBioRunWellMetrics.well_status == "Complete")
            .where(PacBioRunWellMetrics.run_complete > look_back_min_date)
            .where(PacBioRunWellMetrics.polymerase_num_reads.is_not(None))
            .where(
                or_(
                    and_(
                        PacBioRunWellMetrics.ccs_execution_mode.in_(
                            ("OffInstrument", "OnInstrument")
                        ),
                        PacBioRunWellMetrics.hifi_num_reads.is_not(None),
                    ),
                    PacBioRunWellMetrics.ccs_execution_mode == "None",
                )
            )
            .order_by(
                PacBioRunWellMetrics.run_complete,
                PacBioRunWellMetrics.pac_bio_run_name,
                PacBioRunWellMetrics.well_label,
            )
        )

        return self.session.execute(query).scalars().all()


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

    # For MySQL it's OK to use case-sensitive comparison operators since
    # its string comparisons for the collation we use are case-insensitive.
    FILTERS: ClassVar = {
        QcFlowStatusEnum.ON_HOLD.name: (QcStateDict.state == "On hold"),
        QcFlowStatusEnum.QC_COMPLETE.name: (QcState.is_preliminary == 0),
        QcFlowStatusEnum.IN_PROGRESS.name: and_(
            QcState.is_preliminary == 1, QcStateDict.state != "On hold"
        ),
        QcFlowStatusEnum.ABORTED.name: or_(
            PacBioRunWellMetrics.well_status.like("Abort%"),
            PacBioRunWellMetrics.well_status.like("Terminat%"),
            PacBioRunWellMetrics.well_status.like("Fail%"),
            PacBioRunWellMetrics.well_status.like("Error%"),
        ),
        QcFlowStatusEnum.UNKNOWN.name: and_(
            PacBioRunWellMetrics.well_status == "Unknown"
        ),
    }

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.forbid

    def create(self) -> PacBioPagedWells:
        """
        Returns `PacBioPagedWells` object that corresponds to the criteria
        specified by the `page_size`, `page_number, and `qc_flow_status`
        attributes.

        The `PacBioWell` objects in `wells` attribute of the returned object
        are sorted in a way appropriate for the requested `qc_flow_status`.
        For the 'in progress' and 'on hold' requests the wells with most recently
        assigned QC states come first. For inbox requests the wells with least
        recent 'run completed' timestamp are listed first. The query for the
        inbox wells looks at runs which completed within the last four weeks.
        For the 'aborted' and 'unknown' queries the wells are sorted in the
        run name alphabetical order.
        """

        wells = []
        if self.qc_flow_status == QcFlowStatusEnum.INBOX:
            recent_wells = WellWh(session=self.mlwh_session).recent_completed_wells()
            wells = self._recent_inbox_wells(recent_wells)
        elif self.qc_flow_status in [
            QcFlowStatusEnum.ABORTED,
            QcFlowStatusEnum.UNKNOWN,
        ]:
            wells = self._aborted_and_unknown_wells()
        else:
            wells = self._get_wells()
            self._add_tracking_info(wells)

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
        return query.where(self.FILTERS[self.qc_flow_status.name])

    def _retrieve_qc_states(self):

        states = self.qcdb_session.execute(self._build_query4status()).scalars().all()
        # Save the number of retrieved rows - needed to page correctly,
        # also needed by the client to correctly set up the paging widget.
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
            db_well = WellWh(session=self.mlwh_session).get_well(
                run_name=well.run_name, well_label=well.label
            )
            if db_well is None:
                # No error if no matching mlwh record is found.
                logging.warning(
                    f"No mlwh record for run '{well.run_name}' well '{well.label}'"
                )
            else:
                well.copy_run_tracking_info(db_well)

    def _recent_inbox_wells(self, recent_wells):

        inbox_wells_indexes = []
        for index, db_well in enumerate(recent_wells):
            in_qc = WellQc(
                session=self.qcdb_session,
                run_name=db_well.pac_bio_run_name,
                well_label=db_well.well_label,
            ).current_qc_state()
            if in_qc is None:
                inbox_wells_indexes.append(index)

        # Save the number of retrieved rows.
        self.total_number_of_items = len(inbox_wells_indexes)

        inbox_wells = []
        # Iterate over indexes of records we want for this page and retrieve data
        # for this page.
        for index in self.slice_data(inbox_wells_indexes):
            inbox_wells.append(recent_wells[index])

        return self._well_models(inbox_wells)

    def _aborted_and_unknown_wells(self):

        wells = (
            self.mlwh_session.execute(
                select(PacBioRunWellMetrics)
                .where(self.FILTERS[self.qc_flow_status.name])
                .order_by(
                    PacBioRunWellMetrics.pac_bio_run_name,
                    PacBioRunWellMetrics.well_label,
                )
            )
            .scalars()
            .all()
        )

        # Save the number of retrieved rows.
        self.total_number_of_items = len(wells)

        return self._well_models(self.slice_data(wells))

    def _well_models(self, db_wells_list):

        # Normally QC data is not available for the inbox, aborted, etc.
        # wells. If some well with a non-inbox status has QC state assigned,
        # the same well will also be retrieved by the 'in progress' or
        # 'on hold' or 'qc complete' queries. However, it is useful to display
        # the QC state if it is available.
        pb_wells = []
        for db_well in db_wells_list:
            attrs = {"run_name": db_well.pac_bio_run_name, "label": db_well.well_label}
            if self.qc_flow_status != QcFlowStatusEnum.INBOX:
                qc_state = WellQc(
                    session=self.qcdb_session,
                    run_name=db_well.pac_bio_run_name,
                    well_label=db_well.well_label,
                ).current_qc_state()
                if qc_state:
                    attrs["qc_state"] = qc_state
            pb_well = PacBioWell.parse_obj(attrs)
            pb_well.copy_run_tracking_info(db_well)
            pb_wells.append(pb_well)

        return pb_wells
