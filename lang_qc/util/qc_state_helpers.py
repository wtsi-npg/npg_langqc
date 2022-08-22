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
import json
from datetime import datetime
from typing import Optional

from npg_id_generation import PacBioEntity
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from lang_qc.db.qc_schema import (
    ProductLayout,
    QcState,
    SeqPlatform,
    SeqProduct,
    SubProduct,
    SubProductAttr,
    User,
)
from lang_qc.db.utils import get_qc_state_dict, get_qc_type
from lang_qc.models.inbox_models import QcStatus


class NotFoundInDatabaseException(Exception):
    """Exception thrown when something is not found in the DB."""


def create_id_product(run_name, well_label):
    return PacBioEntity(run_name=run_name, well_label=well_label).hash_product_id()


def create_well_properties(run_name, well_label):
    return json.dumps({"run_name": run_name, "well_label": well_label})


def create_well_properties_digest(run_name, well_label):
    return PacBioEntity(run_name=run_name, well_label=well_label).hash_product_id()


def get_seq_product_for_well(run_name: str, well_label: str, qcdb_session: Session):
    """Get a SeqProduct for a well from the QC database.

    This assumes that there is a 1-1 mapping between SubProduct and SeqProduct.
    Args:
        run_name: The run name.
        well_label: The well label.
        qcdb_session: A SQLAlchemy Session connected to the QC database.

    Returns:
        The SeqProduct corresponding to the well.
    """
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


def get_qc_state_for_well(
    run_name: str, well_label: str, qcdb_session: Session
) -> Optional[QcState]:
    """Get a QcState from a well.

    Args:
        run_name: The run name.
        well_label: The well label.
        qcdb_session: A SQLAlchemy Session connected to the QC database.

    Returns:
        Either a QcState object if one is found, or None if not.
    """
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


def construct_seq_product_for_well(
    run_name: str, well_label: str, qcdb_session: Session
):
    """Construct a SeqProduct for a well and push it to the database.

    This assumes a 1-1 mapping between SeqProduct and SubProduct.

    Args:
        run_name: The run name.
        well_label: The well label.
        qcdb_session: A SQLAlchemy Session connected to the QC database.

    Returns:
        The SeqProduct which has been pushed to the QC database.
    """

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
    return seq_product


def update_qc_state(
    qc_status_post: QcStatus, qc_state_db: QcState, user: User, qcdb_session: Session
):
    """Update the properties of the QcState, without pushing the changes.

    Args:
        qc_status_post: The object containing the new properties to update.
        qc_state_db: The object on which to apply the updates.
        qcdb_session: A SQLAlchemy Session connected to the QC database.

    Returns:
        None
    """
    # Check that values are in the DB.
    desired_qc_state_dict = get_qc_state_dict(qc_status_post.qc_state, qcdb_session)
    if desired_qc_state_dict is None:
        raise NotFoundInDatabaseException(
            "Desired QC state is not in the QC database. It might not be allowed."
        )

    qc_type = get_qc_type(qc_status_post.qc_type, qcdb_session)
    if qc_type is None:
        raise NotFoundInDatabaseException("QC type is not in the QC database.")

    qc_state_db.user = user
    qc_state_db.date_updated = datetime.now()
    qc_state_db.id_qc_state_dict = desired_qc_state_dict.id_qc_state_dict
    qc_state_db.id_qc_type = qc_type.id_qc_type
    qc_state_db.created_by = "LangQC"
    qc_state_db.is_preliminary = qc_status_post.is_preliminary


def qc_status_json(db_qc_state: QcState) -> QcStatus:
    """Convenience function to convert a DB QcState to a Pydantic QcStatus.

    Args:
        db_qc_state: the DB QcState object

    Returns:
        A QcStatus object with the properties from the DB QCState record.
    """

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
