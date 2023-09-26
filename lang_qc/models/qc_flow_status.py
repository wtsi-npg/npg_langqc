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

from enum import Enum, unique
from typing import List

from pydantic import BaseModel, Field


class QcFlowStatus(BaseModel):
    """
    A representation of a single QC flow status.

    The QC flow status might encapsulate multiple QC states. It might
    correspond to an unknown (not yet assigned) QC state.
    """

    label: str = Field(title="A human readable label of the status")
    param: str = Field(
        title="""
        A query parameter that should be used to retrieve wells
        at this stage of the flow.
        """
    )


@unique
class QcFlowStatusEnum(str, Enum):
    """
    An enumeration of known QC flow statuses. The order of the statuses is
    consistent with the temporal flow of the manual QC process.

    Logically the upcoming status should be in the beginning. In order
    to keep the order of tab consistent with early versions and to separate
    this status from more relevant to teh QC process statuses, this status
    is placed at the end.
    """

    INBOX = "inbox"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    QC_COMPLETE = "qc_complete"
    ABORTED = "aborted"
    UNKNOWN = "unknown"
    UPCOMING = "upcoming"

    @classmethod
    def qc_flow_statuses(cls) -> "List[QcFlowStatus]":
        """
        A class method that returns a list of QcFlowStatus objects, which
        correspond to known QC flow statuses. The list is ordered in the
        the same way as the enumeration itself.
        """

        statuses = []
        for name, member in cls.__members__.items():
            label = name.replace("_", " ").title().replace("Qc", "QC")
            statuses.append(QcFlowStatus(label=label, param=member))

        return statuses
