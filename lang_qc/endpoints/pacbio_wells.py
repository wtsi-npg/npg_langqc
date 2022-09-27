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
from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends
from ml_warehouse.schema import PacBioRunWellMetrics
from sqlalchemy.orm import Session

from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import QcState
from lang_qc.db.utils import (
    extract_well_label_and_run_name_from_state,
    get_in_progress_wells_and_states,
    get_inbox_wells_and_states,
    get_on_hold_wells_and_states,
    get_qc_complete_wells_and_states,
)
from lang_qc.models.inbox_models import (
    FilteredInboxResultEntry,
    FilteredInboxResults,
    FilteredWellInfo,
    QcStatus,
    QcStatusEnum,
    RunName,
    WellLabel,
)

router = APIRouter()


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

        if run_name not in packed_wells:
            packed_wells[run_name] = {}

        if well_label not in packed_wells[run_name]:
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
        raw_wells = raw_wells_dict.values()
        first_well = next(iter(raw_wells))
        time_start = first_well.metrics.run_start
        time_complete = first_well.metrics.run_complete
        results.append(
            FilteredInboxResultEntry(
                run_name=run_name,
                # There will always be at least one well in a run.
                time_start=time_start,
                time_complete=time_complete,
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

    match status:
        case QcStatusEnum.INBOX:
            return get_inbox_wells_and_states(qcdb_session, mlwh_session, weeks=weeks)
        case QcStatusEnum.IN_PROGRESS:
            return get_in_progress_wells_and_states(qcdb_session, mlwh_session)
        case QcStatusEnum.ON_HOLD:
            return get_on_hold_wells_and_states(qcdb_session, mlwh_session)
        case QcStatusEnum.QC_COMPLETE:
            return get_qc_complete_wells_and_states(qcdb_session, mlwh_session)
        case _:
            raise Exception("An unknown filter was passed.")


@router.get("/wells", response_model=FilteredInboxResults, tags=["Well inbox"])
def get_wells_filtered_by_status(
    qc_status: QcStatusEnum = QcStatusEnum.INBOX,
    weeks: int = 1,
    qcdb_session: Session = Depends(get_qc_db),
    mlwh_session: Session = Depends(get_mlwh_db),
):

    wells, states = grab_wells_with_status(qc_status, qcdb_session, mlwh_session, weeks)
    return pack_wells_and_states(wells, states)
