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
    QcStateDict,
    QcStateHist,
    QcType,
    User,
)
from lang_qc.models.inbox_models import QcStatus
from lang_qc.util.qc_state_helpers import (
    get_seq_product_for_well,
    get_qc_state_for_well,
    construct_seq_product_for_well,
    qc_status_json,
    update_qc_state,
    NotFoundInDatabaseException,
)
from lang_qc.models.qc_state_models import QcStatusAssignmentPostBody, QcClaimPostBody


router = APIRouter()


@router.post(
    "/run/{run_name}/well/{well_label}/qc_claim",
    tags=["Well level QC operations"],
    response_model=QcStatus,
)
def claim_well(
    run_name: str,
    well_label: str,
    body: QcClaimPostBody,
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
) -> QcStatus:

    qcdb_session.begin()
    qc_state = get_qc_state_for_well(run_name, well_label, qcdb_session)

    if qc_state is not None:
        raise HTTPException(
            status_code=400, detail="The well has already been claimed."
        )

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
                status_code=404,
                detail=f"Well {well_label} from run {run_name} is"
                " not in the MLWH database.",
            )

    # Create a SeqProduct and related things for the well.
    seq_product = construct_seq_product_for_well(run_name, well_label, qcdb_session)

    user = qcdb_session.execute(
        select(User).where(User.username == body.user)
    ).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="User has not been found in the QC database. Have they been registered?",
        )

    qc_type = qcdb_session.execute(
        select(QcType).where(QcType.qc_type == "library")
    ).scalar_one_or_none()
    if qc_type is None:
        raise HTTPException(
            status_code=400, detail="QC type is not in the QC database."
        )

    qc_state_dict = qcdb_session.execute(
        select(QcStateDict).where(QcStateDict.state == "Claimed")
    ).scalar_one_or_none()
    if qc_state_dict is None:
        raise HTTPException(
            status_code=400, detail="QC state dict is not in the QC database."
        )

    qc_state = QcState(
        created_by="LangQC",
        is_preliminary=True,
        qc_state_dict=qc_state_dict,
        qc_type=qc_type,
        seq_product=seq_product,
        user=user,
    )

    qcdb_session.add(qc_state)
    qcdb_session.commit()

    return qc_status_json(qc_state)


@router.post(
    "/run/{run_name}/well/{well_label}/qc_assign",
    tags=["Well level QC operations"],
    response_model=QcStatus,
)
def assign_qc_status(
    run_name: str,
    well_label: str,
    request_body: QcStatusAssignmentPostBody,
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
) -> QcStatus:

    qcdb_session.begin()
    qc_state = get_qc_state_for_well(run_name, well_label, qcdb_session)

    if qc_state is None:
        # 400 if unclaimed, 404 if the well does not even exist.
        if (
            mlwhdb_session.execute(
                select(PacBioRunWellMetrics).filter(
                    and_(
                        PacBioRunWellMetrics.well_label == well_label,
                        PacBioRunWellMetrics.pac_bio_run_name == run_name,
                    )
                )
            ).one_or_none()
            is None
        ):
            raise HTTPException(
                status_code=404,
                detail=f"Well {well_label} from run {run_name} is not in the MLWH database.",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Cannot assign a state to a well which has not yet been claimed.",
            )

    # Check if well has been claimed by another user.
    if qc_state.user.username != request_body.user:

        # Maybe they aren't even allowed to do things.

        if (
            qcdb_session.execute(
                select(User).where(User.username == request_body.user)
            ).scalar_one_or_none()
            is None
        ):
            raise HTTPException(
                status_code=400,
                detail="An error occured: User has not been found in the QC database. "
                "Have they been registered?\n"
                f"Request body was: {request_body.json()}",
            )
        raise HTTPException(
            status_code=401,
            detail="Cannot assign a state to a well which has been claimed by another user.",
        )

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

    try:
        update_qc_state(request_body, qc_state, qcdb_session)
    except NotFoundInDatabaseException as e:
        raise HTTPException(
            status_code=400,
            detail=f"An error occured: {str(e)}\nRequest body was: {request_body.json()}",
        )

    qcdb_session.commit()

    return qc_status_json(qc_state)
