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

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from lang_qc.db.helper.qc import BulkQcFetch
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.models.qc_state import QcState

router = APIRouter(
    prefix="/products",
    tags=["product"],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected error"}
    },
)

CHECKSUM_RE = re.compile("^[a-fA-F0-9]{64}$")


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
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Invalid checksum"}
    },
    response_model=dict[str, list[QcState]],
)
def bulk_qc_fetch(request_body: list[str], qcdb_session: Session = Depends(get_qc_db)):
    # Validate body as checksums, because pydantic validators seem to be buggy
    # for root types and lose the valid checksums
    for sha in request_body:
        if not CHECKSUM_RE.fullmatch(sha):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Checksum must be hexadecimal of length 64",
            )
    return BulkQcFetch(session=qcdb_session).query_by_id_list(request_body)
