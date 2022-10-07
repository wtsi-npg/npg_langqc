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

from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from ml_warehouse.schema import PacBioRun, PacBioRunWellMetrics
from pydantic import PositiveInt
from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from starlette import status

from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import QcState as QcStateDB
from lang_qc.db.qc_schema import QcStateHist as QcStateDBHist
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
from lang_qc.models.lims import Sample, Study
from lang_qc.models.pacbio.run import PacBioRunResponse
from lang_qc.models.pacbio.well import InboxResultEntry, WellInfo
from lang_qc.models.qc_flow_status import QcFlowStatusEnum
from lang_qc.models.qc_state import QcClaimPostBody, QcState, QcStatusAssignmentPostBody
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
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected error"}
    },
)


@router.get(
    "/wells",
    summary="Get a list of runs with wells filtered by status",
    description="""
         Taking an optional 'qc_status' as a query parameter, returns a list of
         runs with wells filtered by status. The default qc status is 'inbox'.
         Possible values for this parameter are defined in QcFlowStatusEnum. For the
         inbox view an optional 'weeks' query parameter can be used, it defaults
         to one week and defines the number of weeks to look back.
    """,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Invalid query parameter value"
        }
    },
    response_model=List[InboxResultEntry],
)
def get_wells_filtered_by_status(
    qc_status: QcFlowStatusEnum = QcFlowStatusEnum.INBOX,
    weeks: PositiveInt = 1,
    qcdb_session: Session = Depends(get_qc_db),
    mlwh_session: Session = Depends(get_mlwh_db),
):

    wells, states = grab_wells_with_status(qc_status, qcdb_session, mlwh_session, weeks)
    return pack_wells_and_states(wells, states)


@router.get(
    "/run/{run_name}/well/{well_label}",
    summary="Get QC data for a well",
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
    summary="Well level QC operation - claim the well to start QC",
    response_model=QcState,
)
def claim_well(
    run_name: str,
    well_label: str,
    body: QcClaimPostBody,
    user=Depends(check_user),
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
) -> QcState:

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

    qc_state = QcStateDB(
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
    summary=["Well level QC operation - assign QC state"],
    response_model=QcState,
)
def assign_qc_status(
    run_name: str,
    well_label: str,
    request_body: QcStatusAssignmentPostBody,
    user=Depends(check_user),
    qcdb_session: Session = Depends(get_qc_db),
) -> QcState:

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
        QcStateDBHist(
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


def pack_wells_and_states(wells, qc_states) -> List[InboxResultEntry]:
    """Pack wells and states together into a list of InboxResultEntry objects.

    If a well does not have a corresponding QC state, it will be set to `None`.
    """

    well_id2well: Dict = {}
    well_id2qc_state: Dict = {}

    for well in wells:
        unique_id = _id_for_well((well.pac_bio_run_name, well.well_label))
        well_id2well[unique_id] = well

    for state in qc_states:

        unique_id = _id_for_well(extract_well_label_and_run_name_from_state(state))
        if unique_id not in well_id2well:
            raise Exception(
                f"A state has been found which does not correspond to a well: {state}"
            )

        well_id2qc_state[unique_id] = QcState(
            user=state.user.username,
            date_created=state.date_created,
            date_updated=state.date_updated,
            qc_type=state.qc_type.qc_type,
            qc_type_description=state.qc_type.description,
            qc_state=state.qc_state_dict.state,
            is_preliminary=state.is_preliminary,
            created_by=state.created_by,
        )

    results: List = []
    # Sort the keys so that the wells are listed in order of
    # run name, then well label.
    for well_id in sorted(well_id2well):
        well = well_id2well[well_id]
        results.append(
            InboxResultEntry(
                run_name=well.pac_bio_run_name,
                time_start=well.run_start,
                time_complete=well.run_complete,
                well=WellInfo(
                    label=well.well_label,
                    start=well.well_start,
                    complete=well.well_complete,
                    qc_status=well_id2qc_state.get(well_id, None),
                ),
            )
        )

    return results


def grab_wells_with_status(
    status: QcFlowStatusEnum,
    qcdb_session: Session,
    mlwh_session: Session,
    weeks: PositiveInt = 1,
) -> Tuple[List[PacBioRunWellMetrics], List[QcState]]:
    """Get wells from the QC DB filtered by QC status."""

    match status:
        case QcFlowStatusEnum.INBOX:
            return get_inbox_wells_and_states(qcdb_session, mlwh_session, weeks=weeks)
        case QcFlowStatusEnum.IN_PROGRESS:
            return get_in_progress_wells_and_states(qcdb_session, mlwh_session)
        case QcFlowStatusEnum.ON_HOLD:
            return get_on_hold_wells_and_states(qcdb_session, mlwh_session)
        case QcFlowStatusEnum.QC_COMPLETE:
            return get_qc_complete_wells_and_states(qcdb_session, mlwh_session)
        case _:
            raise Exception("An unknown filter was passed.")


def _id_for_well(run_well: Tuple) -> str:

    return ":".join(run_well)
