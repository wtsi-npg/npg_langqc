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

from fastapi import APIRouter, Depends, HTTPException
from pydantic import PositiveInt
from sqlalchemy.orm import Session
from starlette import status

from lang_qc.db.helper.qc import (
    assign_qc_state_to_product,
    claim_qc_for_product,
    qc_state_for_product_exists,
)
from lang_qc.db.helper.well import well_seq_product_find_or_create
from lang_qc.db.helper.wells import PacBioPagedWellsFactory, WellWh
from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import User
from lang_qc.models.pacbio.well import PacBioPagedWells, PacBioWellFull
from lang_qc.models.qc_flow_status import QcFlowStatusEnum
from lang_qc.models.qc_state import QcState, QcStateBasic
from lang_qc.util.auth import check_user
from lang_qc.util.errors import (
    InconsistentInputError,
    InvalidDictValueError,
    RunNotFoundError,
)
from lang_qc.util.type_checksum import ChecksumSHA256

"""
A collection of API endpoints that are specific to the PacBio sequencing
platform. All URLs start with /pacbio/.

The URLs starting with /pacbio/products are reserved for either retrieving,
or updating, or creating any information about a PacBio product. Sequence
data are out of scope. QC metrics and states and links to any relevant third
party web applications are in scope.

For the purpose of this API the term 'product' has dual semantics. It refers
to either of the entities listed below:
  1. the target product the user is getting as the output of NPG own and
     third party pipelines,
  2. any intermediate product that is used to assess the quality of the end
     product, a single well being the prime example of this.

Each product is characterised by a unique product ID, see
https://github.com/wtsi-npg/npg_id_generation

A non-indexed single library sequenced in a well has the same product ID as
the well product. Therefore, in order to serve the correct response, it is
necessary to know the context of the request. This can be achieved by
different means:
  1. by adding an extra URL component (see /products/{id_product}/seq_level
     URL defined in this package),
  2. by adding an extra parameter to the URL,
  3. for POST requests, by adding and a special field to the payload (see qc_type
     in models in lang_qc.models.qc_state).
"""


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
         Possible values for this parameter are defined in QcFlowStatusEnum.

         The list is paged according to non-optional parameters `page_size` and
         `page_number`.
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
    ).create_for_qc_status(qc_status)


@router.get(
    "/run/{run_name}",
    summary="Get a list of wells for a run",
    description="""
    Returns a list of wells that belong to the run with the run name
    given by the last component of the URL.
    The list is paged according to optional parameters `page_size` and
    `page_number`, which default to 20 and 1 respectively. For the
    majority of runs all wells will fit into the first page of the
    default size.
    """,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Run not found"},
    },
    response_model=PacBioPagedWells,
)
def get_wells_in_run(
    run_name: str,
    page_size: PositiveInt = 20,
    page_number: PositiveInt = 1,
    qcdb_session: Session = Depends(get_qc_db),
    mlwh_session: Session = Depends(get_mlwh_db),
):

    response = None
    try:
        response = PacBioPagedWellsFactory(
            qcdb_session=qcdb_session,
            mlwh_session=mlwh_session,
            page_size=page_size,
            page_number=page_number,
        ).create_for_run(run_name)
    except RunNotFoundError as err:
        raise HTTPException(404, detail=f"{err}")
    return response


@router.get(
    "/products/{id_product}/seq_level",
    summary="Get full sequencing QC metrics and state for a product",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Well product does not exist"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Invalid product ID"},
    },
    response_model=PacBioWellFull,
)
def get_seq_metrics(
    id_product: ChecksumSHA256,
    mlwhdb_session: Session = Depends(get_mlwh_db),
    qcdb_session: Session = Depends(get_qc_db),
) -> PacBioWellFull:

    mlwh_well = _find_well_product_or_error(id_product, mlwhdb_session)

    return PacBioWellFull.from_orm(mlwh_well, qcdb_session)


@router.post(
    "/products/{id_product}/qc_claim",
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
    id_product: ChecksumSHA256,
    user: User = Depends(check_user),
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
) -> QcState:

    mlwh_well = _find_well_product_or_error(id_product, mlwhdb_session)

    # Checking for any type of QC state
    if qc_state_for_product_exists(qcdb_session, id_product):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Well for product {id_product} has QC state assigned",
        )

    claimed_qc_state = claim_qc_for_product(
        session=qcdb_session,
        seq_product=well_seq_product_find_or_create(
            session=qcdb_session, mlwh_well=mlwh_well
        ),
        user=user,
    )
    return QcState.from_orm(claimed_qc_state)


@router.put(
    "/products/{id_product}/qc_assign",
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
    id_product: ChecksumSHA256,
    request_body: QcStateBasic,
    user: User = Depends(check_user),
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
) -> QcState:

    mlwh_well = _find_well_product_or_error(id_product, mlwhdb_session)

    if (
        qc_state_for_product_exists(qcdb_session, id_product, request_body.qc_type)
        is False
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="QC state of an unclaimed well cannot be updated",
        )

    new_qc_state = None
    try:
        new_qc_state = assign_qc_state_to_product(
            session=qcdb_session,
            seq_product=well_seq_product_find_or_create(
                session=qcdb_session, mlwh_well=mlwh_well
            ),
            qc_state=request_body,
            user=user,
        )
    except (InvalidDictValueError, InconsistentInputError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )

    return QcState.from_orm(new_qc_state)


def _find_well_product_or_error(id_product, mlwhdb_session):

    mlwh_well = WellWh(session=mlwhdb_session).get_mlwh_well_by_product_id(
        id_product=id_product
    )
    if mlwh_well is None:
        raise HTTPException(
            404, detail=f"PacBio well for product ID {id_product} not found."
        )
    return mlwh_well
