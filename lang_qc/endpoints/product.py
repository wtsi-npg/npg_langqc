# Copyright (c) 2023 Genome Research Ltd.
#
# Authors:
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

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from lang_qc.db.helper.qc import get_qc_states, get_qc_states_by_id_product_list
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.models.qc_state import QcState
from lang_qc.util.type_checksum import ChecksumSHA256

RECENTLY_QCED_NUM_WEEKS = 4

router = APIRouter(
    prefix="/products",
    tags=["product"],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected error"}
    },
)


@router.post(
    "/qc",
    summary="Returns product QC states for a list of product IDs",
    description="""
    The response is an object whose keys are the given product IDs,
    and the values are lists of QcState records of any type.

    An invalid product ID, which should be a hexadecimal of length 64,
    triggers an error response.

    Product IDs for which no QC states are available are omitted
    from the response. The response may be an empty object.

    This API endpoint is used by the ml warehouse loader for PacBio data, see
    https://github.com/wtsi-npg/npg_ml_warehouse/blob/49.0.0/lib/npg_warehouse/loader/pacbio/qc_state.pm
    """,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Invalid product ID"}
    },
    response_model=dict[ChecksumSHA256, list[QcState]],
)
def bulk_qc_fetch(
    request_body: list[ChecksumSHA256], qcdb_session: Session = Depends(get_qc_db)
):

    return get_qc_states_by_id_product_list(session=qcdb_session, ids=request_body)


@router.get(
    "/qc",
    summary="Returns a dictionary of QC states",
    description="""
    The response is a dictionary of lists of QcState models hashed on product IDs.
    Multiple QC states for the same product might be returned if the query is not
    constrained to a single QC type.

    Query parameters constrain the semantics of the response.
        `weeks`  - number of weeks to look back, defaults to four.
        `seq_level` - a boolean option. If `True`, only `sequencing` type QC states
            are returned. If `False` (the default), all types of QC states are
            returned.
        `final` - a boolean option. If `True`, only final QC states are returned.
            If `False` (the default), both final and preliminary QC states are
            returned.
    """,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Invalid number of weeks"}
    },
    response_model=dict[ChecksumSHA256, list[QcState]],
)
def qc_fetch(
    weeks: Annotated[int, Query(gt=0)] = RECENTLY_QCED_NUM_WEEKS,
    seq_level: bool = False,
    final: bool = False,
    qcdb_session: Session = Depends(get_qc_db),
) -> dict[ChecksumSHA256, list[QcState]]:
    return get_qc_states(
        session=qcdb_session,
        num_weeks=weeks,
        sequencing_outcomes_only=seq_level,
        final_only=final,
    )
