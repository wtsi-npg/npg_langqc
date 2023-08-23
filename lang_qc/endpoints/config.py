# Copyright (c) 2022, 2023 Genome Research Ltd.
#
# Author: Marina Gourtovaia <mg8@sanger.ac.uk>
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

from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lang_qc.db.helper.qc import qc_state_dict
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.models.qc_flow_status import QcFlowStatusEnum

router = APIRouter(
    prefix="/config",
    tags=["config"],
)


@router.get(
    "",
    summary="A helper for the front end renderer.",
    description="""
    Returns a dictionary with configuration options.

    Under the `qc_flow_states` key returns a list of QcFlowStatus objects,
    which corresponds to known QC flow states. The list is sorted in the temporal
    order of the manual QC process. To ensure that the UI is in synch with the
    back end, this list can be used by the frontend code.

    Under the `qc_states` key returns a list of QC states, which should be
    possible to assign via the UI. Each QC state is a dictionary with two entries,
    a `description` and a boolean flag `only_prelim`. This flag is set to `True`
    for those QC dictionary states that cannot be final.
    """,
    response_model=Dict,
)
def get_config(
    session: Session = Depends(get_qc_db),
):

    return {
        "qc_flow_statuses": QcFlowStatusEnum.qc_flow_statuses(),
        "qc_states": _states_for_update(session),
    }


def _states_for_update(session) -> List:

    states = []
    for (name, row) in qc_state_dict(session).items():
        if name not in ["Aborted", "Claimed"]:
            states.append({"description": name, "only_prelim": row.state == "On hold"})

    return states
