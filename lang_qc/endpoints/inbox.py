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

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from ml_warehouse.schema import PacBioRunWellMetrics
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from lang_qc.connection import get_mlwh_db
from lang_qc.models import InboxResults, InboxResultEntry, WellInfo

router = APIRouter()


@router.get("/inbox", response_model=InboxResults)
def get_inbox(weeks: int, db_session: Session = Depends(get_mlwh_db)) -> InboxResults:
    """Get inbox of PacBio runs"""

    stmt = select(PacBioRunWellMetrics).filter(
        and_(
            PacBioRunWellMetrics.polymerase_num_reads is not None,
            or_(
                and_(
                    PacBioRunWellMetrics.ccs_execution_mode.in_(
                        ("OffInstrument", "OnInstrument")
                    ),
                    PacBioRunWellMetrics.hifi_num_reads is not None,
                ),
                PacBioRunWellMetrics.ccs_execution_mode == "None",
            ),
            PacBioRunWellMetrics.well_status == "Complete",
            PacBioRunWellMetrics.well_complete.between(
                datetime.now() - timedelta(weeks=weeks), datetime.now()
            ),
        )
    )

    results: List[PacBioRunWellMetrics] = db_session.execute(stmt).scalars().all()

    grouped = {}

    for well_metrics in results:
        run_name = well_metrics.pac_bio_run_name
        if run_name not in grouped:
            grouped[run_name] = []
        grouped[run_name].append(well_metrics)

    def map_function(well_metrics: List[PacBioRunWellMetrics]) -> InboxResultEntry:
        run_name, well_metrics = well_metrics  # unpack the grouped
        run_name = well_metrics[0].pac_bio_run_name
        time_start = well_metrics[0].run_start
        time_complete = well_metrics[0].run_complete

        wells = sorted(
            map(
                lambda well: WellInfo(
                    label=well.well_label,
                    start=well.well_start,
                    complete=well.well_complete,
                ),
                well_metrics,
            ),
            key=lambda well: well.label,
        )

        return InboxResultEntry(
            run_name=run_name,
            time_start=time_start,
            time_complete=time_complete,
            wells=list(wells),
        )

    mapped = map(map_function, grouped.items())

    output = sorted(
        mapped,
        key=lambda x: max(x.wells, key=lambda y: y.complete).complete,
        reverse=True,
    )
    return output
