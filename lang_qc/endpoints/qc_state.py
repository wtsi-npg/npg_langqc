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

from fastapi import APIRouter, Depends, HTTPException
from ml_warehouse.schema import PacBioRunWellMetrics
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import (
    QcState,
    QcStateHist,
)
from lang_qc.models.inbox_models import QcStatus
from lang_qc.util.qc_state_helpers import (
    get_seq_product_for_well,
    get_qc_state_for_well,
    construct_seq_product_for_well,
    qc_status_json,
    update_qc_state,
)

router = APIRouter()


@router.post(
    "/run/{run_name}/well/{well_label}/qc_assign",
    tags=["Well level QC operations"],
    response_model=QcStatus,
)
def assign_qc_status(
    run_name: str,
    well_label: str,
    qc_status: QcStatus,
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
) -> QcStatus:

    qc_state = get_qc_state_for_well(run_name, well_label, qcdb_session)

    if qc_state is None:

        seq_product = get_seq_product_for_well(run_name, well_label, qcdb_session)

        if seq_product is None:
            # Check that well exists in mlwh
            mlwh_well = mlwhdb_session.execute(
                select(PacBioRunWellMetrics).where(
                    and_(
                        PacBioRunWellMetrics.pac_bio_run_name == run_name,
                        PacBioRunWellMetrics.well_label == well_label,
                    )
                )
            ).scalar()
            if mlwh_well is None:
                raise HTTPException(
                    status_code=400, detail="Well is not in the MLWH database."
                )

            # Create a SeqProduct and related things for the well.
            seq_product = construct_seq_product_for_well(
                run_name, well_label, qcdb_session
            )

        qc_state = QcState(
            seq_product=seq_product,
        )

    else:
        # time to add a historical entry
        qcdb_session.add(
            QcStateHist(
                id_seq_product=qc_state.id_seq_product,
                id_user=qc_state.id_user,
                id_qc_state_dict=qc_state.id_qc_state_dict,
                id_qc_type=qc_state.id_qc_type,
                created_by=qc_state.created_by,
                date_created=qc_state.date_created,
                date_updated=qc_state.date_updated,
                is_preliminary=qc_state.is_preliminary,
            )
        )
        qcdb_session.commit()

    try:
        update_qc_state(qc_status, qc_state, qcdb_session)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    qcdb_session.merge(qc_state)
    qcdb_session.commit()

    return qc_status_json(qc_state)
