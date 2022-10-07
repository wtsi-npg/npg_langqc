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

from pydantic import BaseModel, Field


class QcStatus(BaseModel):
    """Represents QC metadata associated with a QC-able entity (usually a well).

    It stores dates, owning user, and QC status for the relevant entity.
    """

    user: str = Field(default=None, title="User owning the QC stte.")
    date_created: datetime = Field(default=None, title="Date created")
    date_updated: datetime = Field(default=None, title="Date updated")
    qc_type: str = Field(default=None, title="QC type")
    qc_type_description: str = Field(default=None, title="QC type description")
    qc_state: str = Field(default=None, title="QC state")
    is_preliminary: bool = Field(default=None, title="Preliminarity of outcome")
    created_by: str = Field(default=None, title="QC State creator")


class QcStatusAssignmentPostBody(BaseModel):
    """Body for the qc_assign endpoint"""

    qc_type: str
    qc_state: str
    is_preliminary: bool


class QcClaimPostBody(BaseModel):
    """Body for the qc_claim endpoint."""

    qc_type: str
