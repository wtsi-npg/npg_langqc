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

from fastapi import APIRouter, Depends, HTTPException
from ml_warehouse.schema import PacBioRun, PacBioRunWellMetrics
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import QcState, QcStateHist
from lang_qc.db.utils import (
    extract_well_label_and_run_name_from_state,
    get_in_progress_wells_and_states,
    get_inbox_wells_and_states,
    get_on_hold_wells_and_states,
    get_qc_complete_wells_and_states,
    get_qc_state_dict,
    get_qc_type,
    get_well_metrics,
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
from lang_qc.models.pacbio_run_models import PacBioRunResponse, Sample, Study
from lang_qc.models.qc_state_models import QcClaimPostBody, QcStatusAssignmentPostBody
from lang_qc.util.auth import check_user
from lang_qc.util.qc_state_helpers import (
    NotFoundInDatabaseException,
    construct_seq_product_for_well,
    get_qc_state_for_well,
    get_seq_product_for_well,
    qc_status_json,
    update_qc_state,
)

router = APIRouter(
    prefix="/pacbio",
    tags=["pacbio"],
)


@router.get(
    "/wells",
    tags=["Listing of wells filtered by status"],
    response_model=FilteredInboxResults,
)
def get_wells_filtered_by_status(
    qc_status: QcStatusEnum = QcStatusEnum.INBOX,
    weeks: int = 1,
    qcdb_session: Session = Depends(get_qc_db),
    mlwh_session: Session = Depends(get_mlwh_db),
):

    wells, states = grab_wells_with_status(qc_status, qcdb_session, mlwh_session, weeks)
    return pack_wells_and_states(wells, states)


@router.get(
    "/run/{run_name}/well/{well_label}",
    tags=["Well QC data"],
    response_model=PacBioRunResponse,
)
def get_pacbio_well(
    run_name: str, well_label: str, db_session: Session = Depends(get_mlwh_db)
) -> PacBioRunResponse:

    stmt = select(PacBioRun).filter(
        and_(PacBioRun.well_label == well_label, PacBioRun.pac_bio_run_name == run_name)
    )

    results: List = db_session.execute(stmt).scalars().all()

    if len(results) == 0:
        raise HTTPException(404, detail="No PacBio well found matching criteria.")
    if len(results) > 1:
        print("WARNING! THERE IS MORE THAN ONE RESULT! RETURING THE FIRST ONE")

    run: PacBioRun = results[0]

    response = PacBioRunResponse(
        run_info=run,
        metrics=run.pac_bio_product_metrics[0].pac_bio_run_well_metrics,
        study=Study(id=run.study.id_study_lims),
        sample=Sample(id=run.sample.id_sample_lims),
    )
    return response


@router.post(
    "/run/{run_name}/well/{well_label}/qc_claim",
    tags=["Well level QC operations"],
    response_model=QcStatus,
)
def claim_well(
    run_name: str,
    well_label: str,
    body: QcClaimPostBody,
    user=Depends(check_user),
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
) -> QcStatus:

    # Fetch "static" data first.

    qc_type = get_qc_type(body.qc_type, qcdb_session)
    if qc_type is None:
        raise HTTPException(
            status_code=400, detail="QC type is not in the QC database."
        )

    qc_state_dict = get_qc_state_dict("Claimed", qcdb_session)
    if qc_state_dict is None:
        raise HTTPException(
            status_code=400, detail="QC state dict is not in the QC database."
        )

    seq_product = get_seq_product_for_well(run_name, well_label, qcdb_session)

    if seq_product is None:
        # Check that well exists in mlwh
        mlwh_well = get_well_metrics(run_name, well_label, mlwhdb_session)
        if mlwh_well is None:
            raise HTTPException(
                status_code=404,
                detail=f"Well {well_label} from run {run_name} is"
                " not in the MLWH database.",
            )

        # Create a SeqProduct and related things for the well.
        seq_product = construct_seq_product_for_well(run_name, well_label, qcdb_session)

    else:
        qc_state = get_qc_state_for_well(run_name, well_label, qcdb_session)

        if qc_state is not None:
            raise HTTPException(
                status_code=400, detail="The well has already been claimed."
            )

    qc_state = QcState(
        created_by="LangQC",
        is_preliminary=True,
        qc_state_dict=qc_state_dict,
        qc_type=qc_type,
        seq_product=seq_product,
        user=user,
    )

    qcdb_session.add(qc_state)
    qcdb_session.commit()

    return qc_status_json(qc_state)


@router.post(
    "/run/{run_name}/well/{well_label}/qc_assign",
    tags=["Well level QC operations"],
    response_model=QcStatus,
)
def assign_qc_status(
    run_name: str,
    well_label: str,
    request_body: QcStatusAssignmentPostBody,
    user=Depends(check_user),
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
) -> QcStatus:

    qc_state = get_qc_state_for_well(run_name, well_label, qcdb_session)

    if qc_state is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot assign a state to a well which has not yet been claimed.",
        )

    # Check if well has been claimed by another user.
    if qc_state.user != user:
        raise HTTPException(
            status_code=401,
            detail="Cannot assign a state to a well which has been claimed by another user.",
        )

    # time to add a historical entry
    qcdb_session.add(
        QcStateHist(
            id_seq_product=qc_state.id_seq_product,
            id_user=qc_state.id_user,
            id_qc_state_dict=qc_state.id_qc_state_dict,
            id_qc_type=qc_state.id_qc_type,
            created_by=qc_state.created_by,
            date_created=qc_state.date_created,
            date_updated=qc_state.date_updated,
            is_preliminary=qc_state.is_preliminary,
        )
    )

    try:
        update_qc_state(request_body, qc_state, user, qcdb_session)
    except NotFoundInDatabaseException as e:
        raise HTTPException(
            status_code=400,
            detail=f"An error occured: {str(e)}\nRequest body was: {request_body.json()}",
        )

    qcdb_session.commit()

    return qc_status_json(qc_state)


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
