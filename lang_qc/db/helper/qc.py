# Copyright (c) 2023 Genome Research Ltd.
#
# Authors:
#  Kieron Taylor <kt19@sanger.ac.uk>
#  Marina Gourtovaia <mg8@sanger.ac.uk>
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

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from lang_qc.db.qc_schema import QcState as QcStateDb
from lang_qc.db.qc_schema import QcStateDict, QcType, SeqProduct, User
from lang_qc.models.qc_state import QcState
from lang_qc.util.type_checksum import ChecksumSHA256


def get_qc_states_by_id_product_list(
    session: Session,
    ids: list[ChecksumSHA256],
    sequencing_outcomes_only: bool = False,
) -> dict[ChecksumSHA256, list[QcState]]:
    """
    Returns a dictionary whose keys are the given product IDs,
    and the values are lists of QcState records of any type
    for the same product.

    If only sequencing type QC states are required, an optional
    argument, sequencing_outcomes_only, should be set to True.
    If this case it is guaranteed that the list of QcState objects
    has only one member.

    Product IDs for which no QC states are available are omitted
    from the response. The response may be an empty dictionary.

    To remain efficient for large lists of product IDs, no input
    validation is performed. The input should be validated by the
    caller.
    """

    return _map_to_qc_state_models(
        seq_products=_get_seq_product_by_id_list(session, ids),
        sequencing_outcomes_only=sequencing_outcomes_only,
    )


def qc_state_for_product_exists(session: Session, id_product: ChecksumSHA256) -> bool:
    """
    A quick method to find out whether any type of QC state is associated
    with the product. Returns True or False.
    """

    query = (
        select(func.count())
        .select_from(SeqProduct)
        .where(SeqProduct.id_product == id_product)
    )
    return bool(session.execute(query).scalar_one())


def _get_seq_product_by_id_list(
    session: Session, ids: list[ChecksumSHA256]
) -> list[SeqProduct]:
    """
    Generates and executes a query for SeqProducts from a list
    of product IDs. Prefetch all related QC states, types, etc.
    """
    query = (
        select(SeqProduct)
        .join(QcStateDb)
        .join(QcType)
        .join(QcStateDict)
        .join(User)
        .where(SeqProduct.id_product.in_(ids))
        .options(
            selectinload(SeqProduct.qc_state).options(
                selectinload(QcStateDb.qc_type),
                selectinload(QcStateDb.user),
                selectinload(QcStateDb.qc_state_dict),
            )
        )
    )
    return session.execute(query).scalars().all()


def _map_to_qc_state_models(
    seq_products: list[SeqProduct], sequencing_outcomes_only: bool = False
) -> dict[ChecksumSHA256, list[QcState]]:
    """
    Given a list of SeqProducts, convert all related QC states into
    QcState response format and hashes them by their product ID.

    If only sequencing type QC states are required, an optional
    argument, sequencing_outcomes_only, should be set to True.
    """
    response = dict()
    for product in seq_products:
        response[product.id_product] = []
        for qc in product.qc_state:
            if sequencing_outcomes_only and (qc.qc_type.qc_type != "sequencing"):
                continue
            response[product.id_product].append(QcState.from_orm(qc))
    return response
