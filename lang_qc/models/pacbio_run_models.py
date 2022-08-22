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

from lang_qc.models.object_models import PacBioRunWellMetrics, Sample, Study


class Well(BaseModel):

    label: str = Field(default=None, title="Well Label")
    uuid_lims: str = Field(default=None, title="LIMS label uuid")

    class Config:
        orm_mode = False


class PacBioLibraryTube(BaseModel):

    id_lims: str = Field(default=None, title="library tube LIMS id")
    uuid: str = Field(default=None, title="library tube uuid")
    name: str = Field(default=None, title="library tube name")

    class Config:
        orm_mode = False


class PacBioRunInfo(BaseModel):

    last_updated: date = Field(default=None)
    recorded_at: date = Field(default=None)
    id_pac_bio_run_lims: str = Field(default=None)
    pac_bio_run_name: str = Field(default=None)
    pipeline_id_lims: str = Field(default=None)
    cost_code: str = Field(default=None)
    well: Well
    pac_bio_library_tube: PacBioLibraryTube

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: Any) -> "PacBioRunInfo":
        obj.well = Well(
            label=getattr(obj, "well_label", None),
            uuid_lims=getattr(obj, "well_uuid_lims", None),
        )

        obj.pac_bio_library_tube = PacBioLibraryTube(
            id_lims=getattr(obj, "pac_bio_library_tube_id_lims", None),
            uuid=getattr(obj, "pac_bio_library_tube_uuid", None),
            name=getattr(obj, "pac_bio_library_tube_name", None),
        )

        return super().from_orm(obj)


class PacBioRunResponse(BaseModel):
    run_info: PacBioRunInfo
    study: Study
    sample: Sample
    metrics: PacBioRunWellMetrics
