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

from lang_qc.db.helper.well import (
    InconsistentInputError,
    InvalidDictValueError,
    WellMetrics,
    WellQc,
)
from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import User
from lang_qc.db.utils import (
    extract_well_label_and_run_name_from_state,
    get_in_progress_wells_and_states,
    get_inbox_wells_and_states,
    get_on_hold_wells_and_states,
    get_qc_complete_wells_and_states,
)
from lang_qc.models.lims import Sample, Study
from lang_qc.models.pacbio.run import PacBioRunResponse
from lang_qc.models.pacbio.well import PacBioPagedWells, PacBioWell
from lang_qc.models.qc_flow_status import QcFlowStatusEnum
from lang_qc.models.qc_state import QcState, QcStateBasic
from lang_qc.util.auth import check_user

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
    response_model=PacBioPagedWells,
)
def get_wells_filtered_by_status(
    page_size: PositiveInt,
    page_number: PositiveInt,
    qc_status: QcFlowStatusEnum = QcFlowStatusEnum.INBOX,
    qcdb_session: Session = Depends(get_qc_db),
    mlwh_session: Session = Depends(get_mlwh_db),
):

    # Page size and number values will be validated at this point.
    paged_pbwells = PacBioPagedWells(
        page_size=page_size, page_number=page_number, qc_flow_status=qc_status
    )
    # Now we are getting all results for a status.
    # Ideally we'd like to get the relevant page straight away.
    wells, states = grab_wells_with_status(qc_status, qcdb_session, mlwh_session)
    pbwells = pack_wells_and_states(wells, states)
    # Now we slice the list and finalize the object.
    paged_pbwells.set_page(pbwells)
    return paged_pbwells  # And return it.


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
        print("WARNING! THERE IS MORE THAN ONE RESULT! RETURNING THE FIRST ONE")

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
    summary="Claim the well to start QC",
    description="""
    Enables the user to initiate manual QC of the well. The resulting QC state
    is flagged as preliminary. Not every authenticated user is allowed to perform QC.

    A prerequisite to starting manual QC is existence of the well record
    in the ml warehouse database.

    Initiating manual QC on a well that already has been claimed or has any
    other QC state is not allowed.
    """,
    responses={
        status.HTTP_201_CREATED: {"description": "Well successfully claimed"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Invalid query parameter value"
        },
        status.HTTP_404_NOT_FOUND: {"description": "Well does not exist"},
        status.HTTP_409_CONFLICT: {"description": "Well has already been claimed"},
    },
    response_model=QcState,
)
# TODO: Can we pass langqc session to check_user, so that it does not have to
# use its own session? The same for assign_qc_state.
def claim_qc(
    run_name: str,
    well_label: str,
    user: User = Depends(check_user),
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
) -> QcState:

    wm = WellMetrics(session=mlwhdb_session, run_name=run_name, well_label=well_label)
    if wm.exists() is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Well {well_label} run {run_name} does not exist",
        )

    well_qc = WellQc(session=qcdb_session, run_name=run_name, well_label=well_label)
    if well_qc.current_qc_state() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Well {well_label} run {run_name} has already been claimed",
        )

    # Using default attributes for almost all arguments.
    # The new QC state will be set as preliminary.
    return QcState.from_orm(well_qc.assign_qc_state(user=user))


@router.post(
    "/run/{run_name}/well/{well_label}/qc_assign",
    summary="Assign QC state to a well",
    description="""
    Enables the user to assign a new QC state to a well. The well QC should
    have been already claimed. The user performing the operation should
    be the user who assigned the current QC state of the well.
    """,
    responses={
        status.HTTP_201_CREATED: {"description": "Well QC state updated"},
        status.HTTP_400_BAD_REQUEST: {"description": "Request details are incorrect"},
        status.HTTP_403_FORBIDDEN: {"description": "User cannot perform QC"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Invalid query parameter value"
        },
        status.HTTP_409_CONFLICT: {"description": "Requested operation is not allowed"},
    },
    response_model=QcState,
)
def assign_qc_state(
    run_name: str,
    well_label: str,
    request_body: QcStateBasic,
    user: User = Depends(check_user),
    qcdb_session: Session = Depends(get_qc_db),
) -> QcState:

    well_qc = WellQc(session=qcdb_session, run_name=run_name, well_label=well_label)
    qc_state = well_qc.current_qc_state()

    if qc_state is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="QC state of an unclaimed well cannot be updated",
        )

    if qc_state.user.username != user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorised, QC is performed by another user",
        )

    qc_state = None
    message = "Error assigning status: "
    try:
        qc_state = well_qc.assign_qc_state(user=user, **request_body.dict())
    except (InvalidDictValueError, InconsistentInputError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message + str(err),
        )

    return QcState.from_orm(qc_state)


def pack_wells_and_states(wells, qc_states) -> List[PacBioWell]:
    """
    Pack wells and QC states together into a list of PacBioWell objects.

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
        well_id2qc_state[unique_id] = QcState.from_orm(state)

    results: List = []
    # Sort the keys so that the wells are listed in order of
    # run name, then well label.
    for well_id in sorted(well_id2well):
        well = well_id2well[well_id]
        results.append(
            PacBioWell(
                label=well.well_label,
                run_name=well.pac_bio_run_name,
                run_start_time=well.run_start,
                run_complete_time=well.run_complete,
                well_start_time=well.well_start,
                well_complete_time=well.well_complete,
                qc_state=well_id2qc_state.get(well_id, None),
            )
        )

    return results


def grab_wells_with_status(
    status: QcFlowStatusEnum,
    qcdb_session: Session,
    mlwh_session: Session,
) -> Tuple[List[PacBioRunWellMetrics], List[QcState]]:
    """Get wells from the QC DB filtered by QC status."""

    match status:
        case QcFlowStatusEnum.INBOX:
            return get_inbox_wells_and_states(qcdb_session, mlwh_session)
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
