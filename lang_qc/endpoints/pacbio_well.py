# Copyright (c) 2022, 2023 Genome Research Ltd.
#
# Authors:
#   Adam Blanchet
#   Marina Gourtovaia <mg8@sanger.ac.uk>
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

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import PositiveInt
from sqlalchemy.orm import Session
from starlette import status

from lang_qc.db.helper.qc import BulkQcFetch
from lang_qc.db.helper.well import InconsistentInputError, InvalidDictValueError, WellQc
from lang_qc.db.helper.wells import PacBioPagedWellsFactory, WellWh
from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import User
from lang_qc.models.pacbio.well import PacBioPagedWells, PacBioWellFull
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

CHECKSUM_RE = re.compile("^[a-fA-F0-9]{64}$")


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

    # Page size and number values will be validated by the constructor.
    return PacBioPagedWellsFactory(
        qcdb_session=qcdb_session,
        mlwh_session=mlwh_session,
        page_size=page_size,
        page_number=page_number,
        qc_flow_status=qc_status,
    ).create()


@router.get(
    "/run/{run_name}/well/{well_label}",
    summary="Get QC data for a well",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Well does not exist"},
    },
    response_model=PacBioWellFull,
)
def get_pacbio_well(
    run_name: str,
    well_label: str,
    mlwhdb_session: Session = Depends(get_mlwh_db),
    qcdb_session: Session = Depends(get_qc_db),
) -> PacBioWellFull:

    well_row = WellWh(session=mlwhdb_session).get_well(
        run_name=run_name, well_label=well_label
    )
    if well_row is None:
        raise HTTPException(
            404, detail=f"PacBio well {well_label} run {run_name} not found."
        )

    return PacBioWellFull.from_orm(well_row, qcdb_session)


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
    status_code=status.HTTP_201_CREATED,
)
def claim_qc(
    run_name: str,
    well_label: str,
    user: User = Depends(check_user),
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
) -> QcState:

    if (
        WellWh(session=mlwhdb_session).well_exists(
            run_name=run_name, well_label=well_label
        )
        is False
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Well {well_label} run {run_name} does not exist",
        )

    well_qc = WellQc(session=qcdb_session, run_name=run_name, well_label=well_label)
    if well_qc.current_qc_state():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Well {well_label} run {run_name} has already been claimed",
        )

    # Using default attributes for almost all arguments.
    # The new QC state will be set as preliminary.
    return QcState.from_orm(well_qc.assign_qc_state(user=user))


@router.put(
    "/run/{run_name}/well/{well_label}/qc_assign",
    summary="Assign QC state to a well",
    description="""
    Enables the user to assign a new QC state to a well. The well QC should
    have been already claimed. The user performing the operation should
    be the user who assigned the current QC state of the well.
    """,
    responses={
        status.HTTP_200_OK: {"description": "Well QC state updated"},
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


@router.post(
    "/products/qc",
    summary="Populates a list of checksums with Well data",
    description="""
    An endpoint for requesting batches of QC states for a list of IDs.
    It will iterate over a list of product ID checksums that uniquely identify
    wells in runs, and respond with an object whose keys are the provided
    checksums and the values are QcState records divided by their qc_type

    Invalid and non-existent IDs will be omitted from the response. The result
    may be an empty object if no valid IDs are found in the request body.
    """,
    response_model=dict[str, dict[str, QcState]],
)
def bulk_qc_fetch(request_body: list[str], qcdb_session: Session = Depends(get_qc_db)):
    # Validate body as checksums, because pydantic validators seem to be buggy
    # for root types and lose the valid checksums
    for sha in request_body:
        if not CHECKSUM_RE.fullmatch(sha):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Checksum must be hexadecimal of length 64, and not {}".format(
                    sha
                ),
            )
    bulk_fetcher = BulkQcFetch(session=qcdb_session)
    products = bulk_fetcher.query_by_id_list(request_body)

    return products
