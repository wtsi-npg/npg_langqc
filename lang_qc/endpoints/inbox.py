# Copyright (c) 2022 Genome Research Ltd.
#
# Author: Adam Blanchet <ab59@sanger.ac.uk>
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

from dataclasses import dataclass
from datetime import datetime, timedelta
from operator import attrgetter
from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from ml_warehouse.schema import PacBioRunWellMetrics
from sqlalchemy import select, and_, not_, or_
from sqlalchemy.orm import Session

from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import (
    QcState,
    SeqProduct,
    SubProduct,
    ProductLayout,
    QcStateDict,
)
from lang_qc.models.inbox_models import (
    FilteredWellInfo,
    FilteredInboxResultEntry,
    FilteredInboxResults,
    InboxResults,
    InboxResultEntry,
    WellInfo,
    WellLabel,
    QcStatus,
    QcStatusEnum,
    RunName,
)

router = APIRouter()


def grab_recent_wells_from_db(
    weeks: int, db_session: Session
) -> List[PacBioRunWellMetrics]:
    """Get wells from the past few weeks from the database."""

    stmt = select(PacBioRunWellMetrics).filter(
        and_(
            PacBioRunWellMetrics.polymerase_num_reads is not None,
            or_(
                and_(
                    PacBioRunWellMetrics.ccs_execution_mode.in_(
                        ("OffInstrument", "OnInstrument")
                    ),
                    PacBioRunWellMetrics.hifi_num_reads is not None,
                ),
                PacBioRunWellMetrics.ccs_execution_mode == "None",
            ),
            PacBioRunWellMetrics.well_status == "Complete",
            PacBioRunWellMetrics.well_complete.between(
                datetime.now() - timedelta(weeks=weeks), datetime.now()
            ),
        )
    )

    return db_session.execute(stmt).scalars().all()


def extract_well_label_and_run_name_from_state(state: QcState):
    return (
        state.seq_product.product_layout[0].sub_product.value_attr_one,
        state.seq_product.product_layout[0].sub_product.value_attr_two,
    )


def get_well_metrics_from_qc_states(
    qc_states: List[QcState], mlwh_db_session: Session
) -> List[PacBioRunWellMetrics]:
    """Get a list of PacBioRunWellMetrics corresponding to QC states."""

    state_info = [
        extract_well_label_and_run_name_from_state(state) for state in qc_states
    ]
    filters = [
        and_(
            PacBioRunWellMetrics.pac_bio_run_name == run_name,
            PacBioRunWellMetrics.well_label == well_label,
        )
        for run_name, well_label in state_info
    ]
    stmt = select(PacBioRunWellMetrics).where(or_(*filters))

    wells: List[PacBioRunWellMetrics] = mlwh_db_session.execute(stmt).scalars()
    return wells


def pack_wells_and_states(wells, qc_states) -> FilteredInboxResults:
    """Pack wells and states together into FilteredInboxResults.

    If a well does not have a corresponding QC state, it will be
    set to `None`.
    """

    @dataclass
    class RawWellWithState:
        """A convenience class to wrap wells and qc state into one."""

        metrics: PacBioRunWellMetrics
        qc_status: QcStatus

    # Start sorting the wells into runs.
    packed_wells: Dict[RunName, Dict[WellLabel, RawWellWithState]] = {}

    for well in wells:

        run_name = well.pac_bio_run_name
        well_label = well.well_label

        if run_name not in packed_wells.keys():
            packed_wells[run_name] = {}

        if well_label not in packed_wells[run_name].keys():
            packed_wells[run_name][well_label] = RawWellWithState(
                metrics=well, qc_status=None
            )
        else:
            raise Exception(
                "Conflicting PacBioRunWellMetrics: \n"
                f"\tleft: {packed_wells[run_name][well_label]}\n"
                f"\tright: {well}"
            )

    # Add the QC states to their corresponding wells.
    for state in qc_states:
        run_name, well_label = extract_well_label_and_run_name_from_state(state)

        if run_name not in packed_wells.keys():
            raise Exception(
                f"A state has been found which does not correspond to a run: {state}"
            )
        if well_label not in packed_wells[run_name].keys():
            raise Exception(
                f"A state has been found which does not correspond to a well: {state}"
            )

        packed_wells[run_name][well_label].qc_status = QcStatus(
            user=state.user.username,
            date_created=state.date_created,
            date_updated=state.date_updated,
            qc_type=state.qc_type.qc_type,
            qc_type_description=state.qc_type.description,
            qc_state=state.qc_state_dict.state,
            is_preliminary=state.is_preliminary,
            created_by=state.created_by,
        )

    # Construct the results
    results: FilteredInboxResults = []

    for run_name, raw_wells_dict in packed_wells.items():
        raw_wells = list(raw_wells_dict.values())
        results.append(
            FilteredInboxResultEntry(
                run_name=run_name,
                # There will always be at least on well in a run.
                time_start=raw_wells[0].metrics.run_start,
                time_complete=raw_wells[0].metrics.run_complete,
                wells=[
                    FilteredWellInfo(
                        label=raw_well.metrics.well_label,
                        start=raw_well.metrics.well_start,
                        complete=raw_well.metrics.well_complete,
                        qc_status=raw_well.qc_status,
                    )
                    for raw_well in raw_wells
                ],
            )
        )

    return results


def grab_wells_with_status(
    status: QcStatusEnum, qcdb_session: Session, mlwh_session: Session, weeks: int = 1
) -> Tuple[List[PacBioRunWellMetrics], List[QcState]]:
    """Get wells from the QC DB filtered by QC status."""

    # This code assumes there is a 1-1 SeqProduct-SubProduct mapping.

    states = []
    wells = []

    match status:
        case QcStatusEnum.INBOX:
            # Get recent wells, then filter out all those that already have a
            # QcStatus in the DB.

            recent_wells = grab_recent_wells_from_db(weeks, mlwh_session)

            stmt = (
                select(QcState)
                .join(SeqProduct)
                .join(ProductLayout)
                .join(SubProduct)
                .where(
                    and_(
                        SubProduct.value_attr_one.in_(
                            [well.pac_bio_run_name for well in recent_wells]
                        ),
                        SubProduct.value_attr_two.in_(
                            [well.well_label for well in recent_wells]
                        ),
                    )
                )
            )

            already_there = [
                extract_well_label_and_run_name_from_state(state)
                for state in qcdb_session.execute(stmt).scalars().all()
            ]

            wells = [
                record
                for record in recent_wells
                if (record.pac_bio_run_name, record.well_label) not in already_there
            ]

        case QcStatusEnum.IN_PROGRESS:
            # Get wells which have a state that is not "On hold" or preliminary.
            states = (
                qcdb_session.execute(
                    select(QcState)
                    .join(QcStateDict)
                    .where(and_(QcStateDict.state != "On hold", QcState.is_preliminary))
                )
                .scalars()
                .all()
            )
            wells = get_well_metrics_from_qc_states(states, mlwh_session)

        case QcStatusEnum.ON_HOLD:
            # Get wells which have a state that is "On hold".
            states = (
                qcdb_session.execute(
                    select(QcState)
                    .join(QcStateDict)
                    .where(QcStateDict.state == "On hold")
                )
                .scalars()
                .all()
            )
            wells = get_well_metrics_from_qc_states(states, mlwh_session)

        case QcStatusEnum.QC_COMPLETE:
            # Get wells which have a state that is not "On hold" or "Claimed" and that
            # is not preliminary.
            states = (
                qcdb_session.execute(
                    select(QcState)
                    .join(QcStateDict)
                    .where(
                        and_(
                            not_(QcState.is_preliminary),
                            not_(QcStateDict.state.in_(["On hold", "Claimed"])),
                        )
                    )
                )
                .scalars()
                .all()
            )

            wells = get_well_metrics_from_qc_states(states, mlwh_session)
            wells = list(wells)
            for well in wells:
                print(well.pac_bio_run_name, well.well_label)

        case _:
            raise Exception("An unknown filter was passed.")

    return (wells, states)


def group_wells_into_inbox_results(well_db_records: List[PacBioRunWellMetrics]):

    # Group the wells by run.
    grouped_wells = {}

    for well_metrics in well_db_records:
        run_name = well_metrics.pac_bio_run_name
        if run_name not in grouped_wells:
            grouped_wells[run_name] = []
        grouped_wells[run_name].append(well_metrics)

    # Next, convert the grouped wells into result entries.
    def make_inbox_result_entry(
        well_metrics: Tuple[str, List[PacBioRunWellMetrics]]
    ) -> InboxResultEntry:
        """Construct an InboxResultEntry from a list of wells"""
        run_name, well_metrics = well_metrics  # unpack the grouped entries
        time_start = well_metrics[0].run_start
        time_complete = well_metrics[0].run_complete

        wells = sorted(
            [
                WellInfo(
                    label=well.well_label,
                    start=well.well_start,
                    complete=well.well_complete,
                )
                for well in well_metrics
            ],
            key=attrgetter("label"),
        )

        return InboxResultEntry(
            run_name=run_name,
            time_start=time_start,
            time_complete=time_complete,
            wells=wells,
        )

    unsorted_results = map(make_inbox_result_entry, grouped_wells.items())

    # Finally, sort the wells by most recently completed well.
    def get_max_date(entry):
        """Get the most recent well completion date for wells in an entry."""

        return max(entry.wells, key=attrgetter("complete")).complete

    output = sorted(
        unsorted_results,
        key=get_max_date,
        reverse=True,
    )

    return output


@router.get(
    "/inbox",
    response_model=InboxResults,
    responses={400: {"description": "Bad Request. Invalid weeks parameter."}},
)
def get_inbox(
    weeks: int = 2, db_session: Session = Depends(get_mlwh_db)
) -> InboxResults:
    """Get inbox of PacBio runs.

    Fetches from the last 2 weeks by default."""

    if weeks < 0:
        raise HTTPException(
            status_code=400, detail="Bad Request. Invalid weeks paramter."
        )

    results: List[PacBioRunWellMetrics] = grab_recent_wells_from_db(weeks, db_session)

    return group_wells_into_inbox_results(results)


@router.get("/wells", response_model=FilteredInboxResults, tags=["Well inbox"])
def get_wells_filtered_by_status(
    qc_status: QcStatusEnum = QcStatusEnum.INBOX,
    qcdb_session: Session = Depends(get_qc_db),
    mlwh_session: Session = Depends(get_mlwh_db),
):

    wells, states = grab_wells_with_status(qc_status, qcdb_session, mlwh_session)
    return pack_wells_and_states(wells, states)
