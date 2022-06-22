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

from fastapi import APIRouter, Depends, HTTPException
from ml_warehouse.schema import PacBioRun
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.models.pacbio_run_models import PacBioRunResponse, Study, Sample


router = APIRouter()


@router.get("/run/{run_name}/well/{well_label}", response_model=PacBioRunResponse)
def get_pacbio_well(
    run_name: str, well_label: str, db_session: Session = Depends(get_mlwh_db)
) -> PacBioRunResponse:

    stmt = select(PacBioRun).filter(
        and_(PacBioRun.well_label == well_label, PacBioRun.pac_bio_run_name == run_name)
    )

    results: List = db_session.execute(stmt).scalars().all()

    if len(results) == 0:
        raise HTTPException(404, detail="No PacBio well found matching criteria.")
    if len(results) > 1:
        print("WARNING! THERE IS MORE THAN ONE RESULT! RETURING THE FIRST ONE")

    run: PacBioRun = results[0]

    response = PacBioRunResponse(
        run_info=run,
        metrics=run.pac_bio_product_metrics[0].pac_bio_run_well_metrics,
        study=Study(id=run.study.id_study_lims),
        sample=Sample(id=run.sample.id_sample_lims),
    )
    return response
