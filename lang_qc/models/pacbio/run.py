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
# this program. If not, see <http://www.gnu.org/licenses/>.rom datetime import date

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from lang_qc.models.lims import Sample, Study
from lang_qc.models.pacbio.qc_data import QCDataWell


class PacBioRunInfo(BaseModel):

    last_updated: date = Field(default=None)
    recorded_at: date = Field(default=None)
    pac_bio_run_name: str = Field(default=None)
    library_type: str = Field(default=None, title="Library_type")
    well_label: str = Field(default=None, title="Well Label")

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: Any) -> "PacBioRunInfo":
        obj.library_type = obj.pipeline_id_lims
        return super().from_orm(obj)


class PacBioRunResponse(BaseModel):
    run_info: PacBioRunInfo
    study: Study
    sample: Sample
    metrics: QCDataWell
