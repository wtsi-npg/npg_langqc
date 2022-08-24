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


class Study(BaseModel):

    id: str = Field(default=None, title="Study ID.")


class Sample(BaseModel):

    id: str = Field(default=None, title="Sample ID")


class PacBioRun(BaseModel):
    pac_bio_run_name: str = Field(
        default=None,
        title="Run Name",
        description="Lims specific identifier for the pacbio run",
    )
    well_label: str = Field(
        default=None,
        title="Well Label",
        description="The well identifier for the plate, A1-H12",
    )
    well_complete: datetime = Field(
        default=None, title="Well Complete", description="Timestamp of well complete"
    )

    class Config:
        orm_mode = True
