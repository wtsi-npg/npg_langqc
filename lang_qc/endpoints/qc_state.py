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
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from ml_warehouse.schema import PacBioRunWellMetrics
from product_id.main import PacBioWell
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import (
    ProductLayout,
    QcState,
    QcStateDict,
    QcStateHist,
    QcType,
    SeqPlatform,
    SeqProduct,
    SubProduct,
    SubProductAttr,
    User,
)
from lang_qc.models.inbox_models import QcStatus
from lang_qc.models.qc_state_models import QcStatusAssignmentPostBody, QcClaimPostBody


router = APIRouter()


def get_qc_state_for_well(
    run_name: str, well_label: str, qcdb_session: Session
) -> Optional[QcState]:
    """Get a QcState from a well."""

    return qcdb_session.execute(
        select(QcState)
        .join(SeqProduct)
        .join(ProductLayout)
        .join(SubProduct)
        .where(
            and_(
                SubProduct.value_attr_one == run_name,
                SubProduct.value_attr_two == well_label,
            )
        )
    ).scalar_one_or_none()


def get_seq_product_for_well(run_name: str, well_label: str, qcdb_session: Session):
    """Get a SeqProduct from a well."""

    return (
        qcdb_session.execute(
            select(SeqProduct)
            .join(ProductLayout)
            .join(SubProduct)
            .where(
                and_(
                    SubProduct.value_attr_one == run_name,
                    SubProduct.value_attr_two == well_label,
                )
            )
        )
        .scalars()
        .one_or_none()
    )


def create_id_product(run_name, well_label):
    return PacBioWell(run_name=run_name, well_label=well_label)


def create_well_properties(run_name, well_label):
    return json.dumps({"run_name": run_name, "well_label": well_label})


def create_well_properties_digest(run_name, well_label):
    return hash(frozenset(create_well_properties(run_name, well_label)))


def construct_seq_product_for_well(
    run_name: str, well_label: str, qcdb_session: Session
):

    seq_platform = qcdb_session.execute(
        select(SeqPlatform).where(SeqPlatform.name == "PacBio")
    ).scalar_one_or_none()
    if seq_platform is None:
        raise Exception("PacBio SeqPlatform is not in the QC database.")

    run_name_product_attr = qcdb_session.execute(
        select(SubProductAttr).where(SubProductAttr.attr_name == "run_name")
    ).scalar_one_or_none()
    if run_name_product_attr is None:
        raise Exception("PacBio run name SubProductAttr is not the QC database.")

    well_label_product_attr = qcdb_session.execute(
        select(SubProductAttr).where(SubProductAttr.attr_name == "well_label")
    ).scalar_one_or_none()
    if well_label_product_attr is None:
        raise Exception("PacBio well label SubProductAttr is not in the QC database.")

    seq_product = SeqProduct(
        id_product=create_id_product(run_name, well_label),
        seq_platform=seq_platform,
        product_layout=[
            ProductLayout(
                sub_product=SubProduct(
                    sub_product_attr=run_name_product_attr,
                    sub_product_attr_=well_label_product_attr,
                    value_attr_one=run_name,
                    value_attr_two=well_label,
                    properties=create_well_properties(run_name, well_label),
                    properties_digest=create_well_properties_digest(
                        run_name, well_label
                    ),
                )
            )
        ],
    )

    qcdb_session.add(seq_product)
    qcdb_session.commit()

    return seq_product


def update_qc_state(
    qc_status_post: QcStatus, qc_state_db: QcState, qcdb_session: Session
):

    # Check that values are in the DB.
    desired_qc_state_dict = qcdb_session.execute(
        select(QcStateDict.id_qc_state_dict).where(
            QcStateDict.state == qc_status_post.qc_state
        )
    ).one_or_none()
    if desired_qc_state_dict is None:
        raise Exception(
            "Desired QC state is not in the QC database. It might not be allowed."
        )

    user = qcdb_session.execute(
        select(User).where(User.username == qc_status_post.user)
    ).scalar_one_or_none()
    if user is None:
        raise Exception(
            "User has not been found in the QC database. Has it been registered?"
        )

    qc_type = qcdb_session.execute(
        select(QcType.id_qc_type).where(QcType.qc_type == qc_status_post.qc_type)
    ).one_or_none()
    if qc_type is None:
        raise Exception("QC type is not in the QC database.")

    qc_state_db.user = user
    qc_state_db.date_updated = datetime.now()
    qc_state_db.id_qc_state_dict = desired_qc_state_dict[0]
    qc_state_db.id_qc_type = qc_type[0]
    qc_state_db.created_by = "LangQC"
    qc_state_db.is_preliminary = qc_status_post.is_preliminary


def qc_status_json(db_qc_state: QcState) -> QcStatus:

    return QcStatus(
        user=db_qc_state.user.username,
        date_created=db_qc_state.date_created,
        date_updated=db_qc_state.date_updated,
        qc_type=db_qc_state.qc_type.qc_type,
        qc_type_description=db_qc_state.qc_type.description,
        qc_state=db_qc_state.qc_state_dict.state,
        is_preliminary=db_qc_state.is_preliminary,
        created_by=db_qc_state.created_by,
    )


def create_qc_state_for_well(run_name, well_label, qcdb_session):
    """Create and insert a QcState for a well into the DB."""


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
):

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

        user = qcdb_session.execute(
            select(User).where(User.username == body.user)
        ).scalar_one_or_none()
        if user is None:
            user = User(username=body.user, iscurrent=True)

        qc_type = qcdb_session.execute(
            select(QcType).where(QcType.qc_type == "library")
        ).scalar_one_or_none()
        if qc_type is None:
            raise HTTPException(
                status_code=400, detail="QC type is not in the QC database."
            )

        qc_state_dict = qcdb_session.execute(
            select(QcStateDict).where(QcStateDict.state == body.qc_state)
        ).scalar_one_or_none()
        if qc_state_dict is None:
            raise HTTPException(
                status_code=400, detail="QC state dict is not in the QC database."
            )

        qc_state = QcState(
            created_by="LangQC",
            is_preliminary=body.is_preliminary,
            qc_state_dict=qc_state_dict,
            qc_type=qc_type,
            seq_product=seq_product,
            user=user,
        )

        qcdb_session.add(qc_state)
        qcdb_session.commit()


@router.post(
    "/run/{run_name}/well/{well_label}/qc_assign",
    tags=["Well level QC operations"],
    response_model=QcStatus,
)
def assign_qc_status(
    run_name: str,
    well_label: str,
    qc_status: QcStatusAssignmentPostBody,
    qcdb_session: Session = Depends(get_qc_db),
    mlwhdb_session: Session = Depends(get_mlwh_db),
):

    qc_state = get_qc_state_for_well(run_name, well_label, qcdb_session)

    if qc_state is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot assign a state to a well which has not yet been claimed.",
        )

    else:
        # Create a historical record
        historical_record = QcStateHist(
            id_seq_product=qc_state.id_seq_product,
            id_qc_type=qc_state.id_qc_type,
            id_user=qc_state.id_user,
            id_qc_state_dict=qc_state.id_qc_state_dict,
            created_by=qc_state.created_by,
            date_created=qc_state.date_created,
            date_updated=qc_state.date_updated,
            is_preliminary=qc_state.is_preliminary,
        )

        qcdb_session.add(historical_record)
        qcdb_session.commit()

        # Update the current record
        try:
            update_qc_state(qc_status, qc_state, qcdb_session)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        qcdb_session.merge(qc_state)
        qcdb_session.commit()

    return qc_status_json(qc_state)
