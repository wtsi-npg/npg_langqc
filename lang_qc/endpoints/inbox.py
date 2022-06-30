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

from datetime import datetime, timedelta
from operator import attrgetter
from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from ml_warehouse.schema import PacBioRunWellMetrics
from sqlalchemy import select, and_, or_
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
    InboxResults,
    InboxResultEntry,
    WellInfo,
    QcStatusEnum,
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

    results: List[PacBioRunWellMetrics] = db_session.execute(stmt).scalars().all()
    return results


def extract_well_label_and_run_name_from_state(state: QcState):
    return (
        state.seq_product.product_layout[0].sub_product.value_attr_one,
        state.seq_product.product_layout[0].sub_product.value_attr_two,
    )


def get_well_metrics_from_qc_states(
    qc_states: List[QcState], mlwh_db_session: Session
) -> List[PacBioRunWellMetrics]:
    state_info = [
        extract_well_label_and_run_name_from_state(state) for state in qc_states
    ]
    run_names = [info[0] for info in state_info]
    well_labels = [info[1] for info in state_info]
    stmt = select(PacBioRunWellMetrics).where(
        and_(
            PacBioRunWellMetrics.pac_bio_run_name.in_(run_names),
            PacBioRunWellMetrics.well_label.in_(well_labels),
        )
    )

    return mlwh_db_session.execute(stmt).scalars()


def grab_wells_with_status(
    status: QcStatusEnum, qcdb_session: Session, mlwh_session: Session, weeks: int = 1
) -> List[PacBioRunWellMetrics]:
    """Get wells from the QC DB filtered by QC status."""

    # This is a bit weird for now. This also assumes there is a 1-1 SeqProduct-SubProduct mapping.
    # From there we have two cases:
    # - these are QC statuses for the wells we want. In this case we get the wells
    #   and display them.
    # - we want the inbox. In this case we have the list of wells which already have
    #   a QC status. Meaning we want to prune these from the results.
    match status:
        case QcStatusEnum.INBOX:
            recent_wells = grab_recent_wells_from_db(weeks, mlwh_session)

            stmt = (
                select(QcState)
                .join(SeqProduct)
                .join(ProductLayout)
                .join(SubProduct)
                .where(
                    # extract_well_label_and_run_name_from_state(QcState)
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

            return [
                record
                for record in recent_wells
                if (record.pac_bio_run_name, record.well_label) not in already_there
            ]

        case QcStatusEnum.IN_PROGRESS:
            states = (
                qcdb_session.execute(
                    select(QcState)
                    .join(QcStateDict)
                    .join(SeqProduct)
                    .join(ProductLayout)
                    .join(SubProduct)
                    .where(QcStateDict.state != "On hold" and QcState.is_preliminary)
                )
                .scalars()
                .all()
            )
            return get_well_metrics_from_qc_states(states, mlwh_session)

        case QcStatusEnum.ON_HOLD:
            states = (
                qcdb_session.execute(
                    select(QcState)
                    .join(QcStateDict)
                    .join(SeqProduct)
                    .join(ProductLayout)
                    .join(SubProduct)
                    .where(QcStateDict.state == "On hold")
                )
                .scalars()
                .all()
            )
            return get_well_metrics_from_qc_states(states, mlwh_session)

        case QcStatusEnum.QC_COMPLETE:
            states = (
                qcdb_session.execute(
                    select(QcState)
                    .join(QcStateDict)
                    .join(SeqProduct)
                    .join(ProductLayout)
                    .join(SubProduct)
                    .where(
                        QcState.is_preliminary
                        and QcStateDict.state not in ["On hold", "Claimed"]
                    )
                )
                .scalars()
                .all()
            )

            return get_well_metrics_from_qc_states(states, mlwh_session)

        case _:
            raise Exception("An unknown filter was passed.")


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


@router.get("/wells", response_model=InboxResults, tags=["Well inbox"])
def get_wells_filtered_by_status(
    qc_status: QcStatusEnum = None,
    qcdb_session: Session = Depends(get_qc_db),
    mlwh_session: Session = Depends(get_mlwh_db),
):

    wells = grab_wells_with_status(qc_status, qcdb_session, mlwh_session)
    return group_wells_into_inbox_results(wells)
