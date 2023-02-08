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
                detail="Checksum must be hexadecimal of length 64",
            )
    bulk_fetcher = BulkQcFetch(session=qcdb_session)
    products = bulk_fetcher.query_by_id_list(request_body)

    return products
