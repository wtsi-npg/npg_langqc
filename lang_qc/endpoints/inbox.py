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
from operator import attrgetter
from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from ml_warehouse.schema import PacBioRunWellMetrics
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.models.inbox_models import InboxResults, InboxResultEntry, WellInfo

router = APIRouter()


def grab_wells_from_db(weeks: int, db_session: Session):
    """Get wells from the past few weeks from the database."""

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
    return results


@router.get(
    "/inbox",
    response_model=InboxResults,
    responses={400: {"description": "Bad Request. Invalid weeks parameter."}},
)
def get_inbox(
    weeks: int = 2, db_session: Session = Depends(get_mlwh_db)
) -> InboxResults:
    """Get inbox of PacBio runs.

    Fetches from the last 2 weeks by default."""

    if weeks < 0:
        raise HTTPException(
            status_code=400, detail="Bad Request. Invalid weeks paramter."
        )

    results: List[PacBioRunWellMetrics] = grab_wells_from_db(weeks, db_session)

    # Group the wells by run.
    grouped_wells = {}

    for well_metrics in results:
        run_name = well_metrics.pac_bio_run_name
        if run_name not in grouped_wells:
            grouped_wells[run_name] = []
        grouped_wells[run_name].append(well_metrics)

    # Next, convert the grouped wells into result entries.
    def make_inbox_result_entry(
        well_metrics: Tuple[str, List[PacBioRunWellMetrics]]
    ) -> InboxResultEntry:
        """Construct an InboxResultEntry from a list of wells"""
        run_name, well_metrics = well_metrics  # unpack the grouped entries
        time_start = well_metrics[0].run_start
        time_complete = well_metrics[0].run_complete

        wells = sorted(
            [
                WellInfo(
                    label=well.well_label,
                    start=well.well_start,
                    complete=well.well_complete,
                )
                for well in well_metrics
            ],
            key=attrgetter("label"),
        )

        return InboxResultEntry(
            run_name=run_name,
            time_start=time_start,
            time_complete=time_complete,
            wells=wells,
        )

    unsorted_results = map(make_inbox_result_entry, grouped_wells.items())

    # Finally, sort the wells by most recently completed well.
    def get_max_date(entry):
        """Get the most recent well completion date for wells in an entry."""

        return max(entry.wells, key=attrgetter("complete")).complete

    output = sorted(
        unsorted_results,
        key=get_max_date,
        reverse=True,
    )

    return output
