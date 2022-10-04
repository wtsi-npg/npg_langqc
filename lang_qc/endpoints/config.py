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

from typing import List

from fastapi import APIRouter

from lang_qc.models.qc_flow_status import QcFlowStatus, QcFlowStatusEnum

router = APIRouter(
    prefix="/config",
    tags=["config"],
)


@router.get(
    "/qc_flow_status",
    summary="Returns known QC flow statuses and their labels.",
    description="""
    A helper for the front end renderer. Returns a sorted list of known
    QcFlowStatus objects. To ensure that the UI is in synch with the back end,
    this list can be used by the frontend code.
    """,
    response_model=List[QcFlowStatus],
)
def get_qc_flow_statuses():

    return QcFlowStatusEnum.qc_flow_statuses()
