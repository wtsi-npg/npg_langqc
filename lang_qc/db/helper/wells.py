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

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from lang_qc.db.helper.qc import (
    get_qc_states_by_id_product_list,
    qc_state_for_products_exists,
)
from lang_qc.db.mlwh_schema import PacBioRunWellMetrics
from lang_qc.db.qc_schema import QcState, QcStateDict, QcType
from lang_qc.models.pacbio.well import PacBioPagedWells, PacBioWell
from lang_qc.models.pager import PagedResponse
from lang_qc.models.qc_flow_status import QcFlowStatusEnum
from lang_qc.models.qc_state import QcState as QcStateModel
from lang_qc.util.errors import EmptyListOfRunNamesError, RunNotFoundError

"""
This package is using an undocumented feature of Pydantic, type
`ClassVar`, which was introduced in https://github.com/pydantic/pydantic/pull/339
Here this type is used to mark a purely internal to the class variables.
"""

INBOX_LOOK_BACK_NUM_WEEKS = 12


class WellWh(BaseModel):
    """
    A data access class for routine SQLAlchemy operations on wells data
    in ml warehouse database.
    """

    session: Session = Field(
        alias="mlwh_session",
        title="SQLAlchemy Session",
        description="A SQLAlchemy Session for the ml warehouse database",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
    # frozen=True from Pydantic v2 does not work the way we want it to during testing.
    # The TestClient seems to be keeping these instances alive and changing them.

    def get_mlwh_well_by_product_id(
        self, id_product: str
    ) -> PacBioRunWellMetrics | None:
        """
        Returns a well row record from the well metrics table or
        None if the record does not exist.
        """

        return self.session.execute(
            select(PacBioRunWellMetrics).where(
                PacBioRunWellMetrics.id_pac_bio_product == id_product,
            )
        ).scalar_one_or_none()

    def recent_completed_wells(self) -> List[PacBioRunWellMetrics]:
        """
        Get recent not QC-ed completed wells from the mlwh database.
        Recent wells are defined as wells that completed within the
        last 12 weeks.
        """

        ######
        # It is important not to show aborted wells in the inbox.
        #
        # The well can be complete, but that's not the same as analysis
        # complete which the other conditions are trying for.
        # It potentially gets a bit easier with v11 but those conditions
        # should still work ok.
        #

        # Using current local time.
        # Generating a date rather than a timestamp here in order to have a consistent
        # earliest date for the look-back period during the QC team's working day.
        my_date = date.today() - timedelta(weeks=INBOX_LOOK_BACK_NUM_WEEKS)
        look_back_min_date = datetime(my_date.year, my_date.month, my_date.day)

        # Select the wells that has not been QC-ed, but later double-check against
        # the LangQC database.

        # TODO: fall back to run_complete when well_complete is undefined

        query = (
            select(PacBioRunWellMetrics)
            .where(PacBioRunWellMetrics.well_status == "Complete")
            .where(PacBioRunWellMetrics.qc_seq_state.is_(None))
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
                PacBioRunWellMetrics.plate_number,
                PacBioRunWellMetrics.well_label,
            )
        )

        return self.session.execute(query).scalars().all()

    def get_wells_in_runs(self, run_names: List[str]) -> List[PacBioRunWellMetrics]:
        """
        Returns a potentially empty list of well records for runs with names
        given by the run_names argument. Errors if the argument run_name is empty
        or undefined.
        """

        if len(run_names) == 0:
            raise EmptyListOfRunNamesError("List of run names cannot be empty.")

        query = (
            select(PacBioRunWellMetrics)
            .where(PacBioRunWellMetrics.pac_bio_run_name.in_(run_names))
            .order_by(
                PacBioRunWellMetrics.pac_bio_run_name,
                PacBioRunWellMetrics.plate_number,
                PacBioRunWellMetrics.well_label,
            )
        )
        return self.session.execute(query).scalars().all()


class PacBioPagedWellsFactory(WellWh, PagedResponse):
    """
    Factory class to create `PacBioPagedWells` objects that correspond to
    the criteria given by the attributes of the object, i.e. `page_size`
    `page_number`, and any other criteria that are specified by the
    arguments of the factory methods of this class.
    """

    qcdb_session: Session = Field(
        title="SQLAlchemy Session",
        description="A SQLAlchemy Session for the LangQC database",
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

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    def create_for_qc_status(
        self, qc_flow_status: QcFlowStatusEnum
    ) -> PacBioPagedWells:
        """
        Returns `PacBioPagedWells` object that corresponds to the criteria
        specified by the `page_size`, `page_number` object's attributes and
        `qc_flow_status` argument of this function..

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
        if qc_flow_status == QcFlowStatusEnum.INBOX:
            recent_wells = self.recent_completed_wells()
            wells = self._recent_inbox_wells(recent_wells)
        elif qc_flow_status in [
            QcFlowStatusEnum.ABORTED,
            QcFlowStatusEnum.UNKNOWN,
        ]:
            wells = self._aborted_and_unknown_wells(qc_flow_status)
        elif qc_flow_status == QcFlowStatusEnum.UPCOMING:
            wells = self._upcoming_wells()
        else:
            wells = self._get_wells_for_status(qc_flow_status)

        return PacBioPagedWells(
            page_number=self.page_number,
            page_size=self.page_size,
            total_number_of_items=self.total_number_of_items,
            wells=wells,
        )

    def create_for_run(self, run_name: str) -> PacBioPagedWells:
        """
        Returns `PacBioPagedWells` object that corresponds to the criteria
        specified by the `page_size` and `page_number` attributes.
        The `PacBioWell` objects in `wells` attribute of the returned object
        belong to runs specified by the `run_name` argument and are sorted
        by the run name and well label.
        """

        wells = self.get_wells_in_runs([run_name])
        total_number_of_wells = len(wells)
        if total_number_of_wells == 0:
            raise RunNotFoundError(f"Metrics data for run '{run_name}' is not found")

        wells = self.slice_data(wells)
        return PacBioPagedWells(
            page_number=self.page_number,
            page_size=self.page_size,
            total_number_of_items=total_number_of_wells,
            wells=self._well_models(wells, True),
        )

    def _build_query4status(self, qc_flow_status: QcFlowStatusEnum):

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
        return query.where(self.FILTERS[qc_flow_status.name])

    def _retrieve_paged_qc_states(
        self, qc_flow_status: QcFlowStatusEnum
    ) -> List[QcState]:

        states = (
            self.qcdb_session.execute(self._build_query4status(qc_flow_status))
            .scalars()
            .all()
        )
        # Save the number of retrieved rows - needed to page correctly,
        # also needed by the client to correctly set up the paging widget.
        self.total_number_of_items = len(states)
        # Return the states for the wells we were asked to fetch, max - page_size, min - 0.
        return self.slice_data(states)

    def _get_wells_for_status(
        self, qc_flow_status: QcFlowStatusEnum
    ) -> List[PacBioWell]:

        wells = []

        for qc_state_db in self._retrieve_paged_qc_states(qc_flow_status):
            qc_state_model = QcStateModel.from_orm(qc_state_db)
            id_product = qc_state_model.id_product
            mlwh_well = self.get_mlwh_well_by_product_id(id_product=id_product)
            if mlwh_well is not None:
                pbw = PacBioWell(
                    id_product=id_product,
                    run_name=mlwh_well.pac_bio_run_name,
                    plate_number=mlwh_well.plate_number,
                    label=mlwh_well.well_label,
                    qc_state=qc_state_model,
                )
                pbw.copy_run_tracking_info(mlwh_well)
                wells.append(pbw)
            else:
                """
                Cannot display this QC state. In production we are unlikely to
                have a record in the QC database without it also being present
                in the MLWH database.
                Note that the total number of items is not updated.
                """
                logging.warning(f"No mlwh record for product ID '{id_product}'")

        return wells

    def _add_tracking_info(self, wells: List[PacBioWell]):

        for well in wells:
            # One query for all or query per well? The latter for now to avoid the need
            # to match the records later. Should be fast enough for small-ish pages, we
            # query on a unique key.
            db_well = self.get_mlwh_well_by_product_id(product_id=well.product_id)
            if db_well is None:
                # No error if no matching mlwh record is found.
                logging.warning(
                    f"No mlwh record for run '{well.run_name}' well '{well.label}'"
                )
            else:
                well.copy_run_tracking_info(db_well)

    def _upcoming_wells(self):
        """
        Upcoming wells are recent wells, which do not belong to any other
        QC flow statuses as defined in QcFlowStatus. Recent wells are defined
        as wells that belong to runs that started within the last 12 weeks.
        """

        recent_completed_product_ids = [
            w.id_pac_bio_product for w in self.recent_completed_wells()
        ]

        my_date = date.today() - timedelta(weeks=INBOX_LOOK_BACK_NUM_WEEKS)
        look_back_min_date = datetime(my_date.year, my_date.month, my_date.day)

        # If queries for any other filters change, this query should be revised
        # since we are repeating (but negating) a few condition that are
        # associated with some of the statuses (filters).

        query = (
            select(PacBioRunWellMetrics)
            .where(PacBioRunWellMetrics.run_start > look_back_min_date)
            .where(PacBioRunWellMetrics.qc_seq_state.is_(None))
            .where(
                PacBioRunWellMetrics.id_pac_bio_product.not_in(
                    recent_completed_product_ids
                )
            )
            .where(PacBioRunWellMetrics.well_status.not_like("Abort%"))
            .where(PacBioRunWellMetrics.well_status.not_like("Terminat%"))
            .where(PacBioRunWellMetrics.well_status.not_like("Fail%"))
            .where(PacBioRunWellMetrics.well_status.not_like("Error%"))
            .where(PacBioRunWellMetrics.well_status.not_in(["Unknown", "On hold"]))
            .order_by(
                PacBioRunWellMetrics.run_start,
                PacBioRunWellMetrics.pac_bio_run_name,
                PacBioRunWellMetrics.plate_number,
                PacBioRunWellMetrics.well_label,
            )
        )

        wells = self.session.execute(query).scalars().all()
        ids_with_qc_state = qc_state_for_products_exists(
            session=self.qcdb_session, ids=[w.id_pac_bio_product for w in wells]
        )
        wells = [w for w in wells if w.id_pac_bio_product not in ids_with_qc_state]

        self.total_number_of_items = len(wells)  # Save the number of retrieved wells.

        return self._well_models(self.slice_data(wells), False)

    def _recent_inbox_wells(self, recent_wells):

        inbox_wells_indexes = []
        for index, db_well in enumerate(recent_wells):
            id_product = db_well.id_pac_bio_product
            # TODO: Create a method for retrieving a seq. QC state for a product.
            qced_products = get_qc_states_by_id_product_list(
                session=self.qcdb_session,
                ids=[id_product],
                sequencing_outcomes_only=True,
            ).get(id_product)
            if qced_products is None:
                inbox_wells_indexes.append(index)

        # Save the number of retrieved rows.
        self.total_number_of_items = len(inbox_wells_indexes)

        inbox_wells = []
        # Iterate over indexes of records we want for this page and retrieve data
        # for this page.
        for index in self.slice_data(inbox_wells_indexes):
            inbox_wells.append(recent_wells[index])

        return self._well_models(inbox_wells)

    def _aborted_and_unknown_wells(self, qc_flow_status: QcFlowStatusEnum):

        wells = (
            self.session.execute(
                select(PacBioRunWellMetrics)
                .where(self.FILTERS[qc_flow_status.name])
                .order_by(
                    PacBioRunWellMetrics.pac_bio_run_name,
                    PacBioRunWellMetrics.plate_number,
                    PacBioRunWellMetrics.well_label,
                )
            )
            .scalars()
            .all()
        )

        # Save the number of retrieved rows.
        self.total_number_of_items = len(wells)

        return self._well_models(self.slice_data(wells), True)

    def _well_models(
        self,
        db_wells_list: List[PacBioRunWellMetrics],
        qc_state_applicable: bool = False,
    ):

        # Normally QC data is not available for the inbox, aborted, etc.
        # wells. If some well with a non-inbox status has QC state assigned,
        # the same well will also be retrieved by the 'in progress' or
        # 'on hold' or 'qc complete' queries. However, it is useful to display
        # the QC state if it is available. The `qc_state_applicable` argument
        # is a hint to fetch QC state.
        pb_wells = []
        for db_well in db_wells_list:
            id_product = db_well.id_pac_bio_product
            attrs = {
                "id_product": id_product,
                "run_name": db_well.pac_bio_run_name,
                "plate_number": db_well.plate_number,
                "label": db_well.well_label,
            }
            if qc_state_applicable:
                # TODO: Query by all IDs at once.
                qced_products = get_qc_states_by_id_product_list(
                    session=self.qcdb_session,
                    ids=[id_product],
                    sequencing_outcomes_only=True,
                ).get(id_product)
                # A well can have only one or zero current sequencing outcomes.
                if qced_products is not None:
                    attrs["qc_state"] = qced_products[0]
            pb_well = PacBioWell.model_validate(attrs)
            pb_well.copy_run_tracking_info(db_well)
            pb_wells.append(pb_well)

        return pb_wells
