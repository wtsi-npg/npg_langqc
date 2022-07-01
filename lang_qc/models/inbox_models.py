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

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class QcStatusEnum(Enum):
    INBOX = "inbox"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    QC_COMPLETE = "qc_complete"


RunName = str
WellLabel = str


class WellInfo(BaseModel):

    label: str = Field(
        default=None, title="Well label", description="The well identifier."
    )
    start: datetime = Field(default=None, title="Timestamp of well started")
    complete: datetime = Field(default=None, title="Timestamp of well complete")


class InboxResultEntry(BaseModel):

    run_name: str = Field(
        default=None,
        title="Run Name",
    )
    time_start: datetime = Field(default=None, title="Run start time")
    time_complete: datetime = Field(default=None, title="Run complete time")
    wells: List[WellInfo]


class InboxResults(BaseModel):

    __root__: List[InboxResultEntry]


class QcStatus(BaseModel):

    user: str = Field(default=None, title="User owning the QC stte.")
    date_created: datetime = Field(default=None, title="Date created")
    date_updated: datetime = Field(default=None, title="Date updated")
    qc_type: str = Field(default=None, title="QC type")
    qc_type_description: str = Field(default=None, title="QC type description")
    is_preliminary: bool = Field(default=None, title="Preliminarity of outcome")
    created_by: str = Field(default=None, title="QC State creator")


class FilteredWellInfo(WellInfo):
    qc_status: QcStatus = Field(default=None, title="Well QC status")


class FilteredInboxResultEntry(InboxResultEntry):

    wells: List[FilteredWellInfo]


class FilteredInboxResults(BaseModel):

    __root__: List[FilteredInboxResultEntry]
