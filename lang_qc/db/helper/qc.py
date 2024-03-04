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

from collections import defaultdict
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, selectinload

from lang_qc.db.qc_schema import QcState as QcStateDb
from lang_qc.db.qc_schema import QcStateDict, QcStateHist, QcType, SeqProduct, User
from lang_qc.models.qc_state import QcState, QcStateBasic
from lang_qc.util.errors import InconsistentInputError, InvalidDictValueError
from lang_qc.util.type_checksum import ChecksumSHA256

"""
A collection of functions for retrieving and assigning QC state
either for an individual product or for a list of products.

All functions are sequencing platform independent.
"""

APPLICATION_NAME = "LangQC"
DEFAULT_QC_TYPE = "sequencing"
SEQUENCING_QC_TYPE = DEFAULT_QC_TYPE
CLAIMED_QC_STATE = "Claimed"
DEFAULT_FINALITY = False
ONLY_PRELIM_STATES = (CLAIMED_QC_STATE, "On hold")


def qc_state_dict(session: Session) -> dict:
    """
    Returns a dictionary of QC state dictionary rows, where the QcStateDict objects
    representing the database rows are values and the string descriptions of the
    state are keys.

    Arguments:
        `session` - `sqlalchemy.orm.Session`, a connection for LangQC database.
    """

    db_states = (
        session.execute(
            select(QcStateDict).order_by(QcStateDict.outcome.desc(), QcStateDict.state)
        )
        .scalars()
        .all()
    )

    return {row.state: row for row in db_states}


def get_qc_states_by_id_product_list(
    session: Session,
    ids: list[ChecksumSHA256],
    sequencing_outcomes_only: bool = False,
) -> dict[ChecksumSHA256, list[QcState]]:
    """
    Returns a dictionary where keys are the given product IDs,
    and the values are lists of QcState records of any type
    for the same product.

    If only sequencing type QC states are required, an optional
    argument, sequencing_outcomes_only, should be set to True.
    In this case it is guaranteed that the list of QcState objects
    has only one member.

    Product IDs for which no QC states are found are omitted
    from the response. The response may be an empty dictionary.

    To remain efficient for large lists of product IDs, no input
    validation is performed. The input should be validated by the
    caller.

    Arguments:
        `session` - `sqlalchemy.orm.Session`, a connection for LangQC database.
        `ids` - a list of string product ID.
        `sequencing_outcomes_only`- a boolean flag, False by default.
    """

    qc_states = _get_qc_state_by_id_list(session, ids, sequencing_outcomes_only)

    response = defaultdict(list)
    for state in qc_states:
        response[state.seq_product.id_product].append(QcState.from_orm(state))

    return dict(response)


def product_has_qc_state(
    session: Session, id_product: ChecksumSHA256, qc_type: str = None
) -> bool:
    """
    A function to find out whether a particular type of QC state
    is associated with the product. Returns True or False.

    If the optional qc_type argument is None, finding a QC state
    for any QC type will result in a True return.

    `InvalidDictValueError` is raised if the argument QC type value
    is not found in the database dictionary of QC types.

    Arguments:
        `session` - `sqlalchemy.orm.Session`, a connection for LangQC database.
        `id_product` - a string product ID.
        `qc_type`- a string QC type.
    """

    query = (
        select(func.count())
        .select_from(SeqProduct)
        .where(SeqProduct.id_product == id_product)
    )
    if qc_type is not None:
        query = query.join(SeqProduct.qc_state).where(
            QcStateDb.qc_type == _get_qc_type_row(session, qc_type)
        )

    return bool(session.execute(query).scalar_one())


def products_have_qc_state(
    session: Session, ids: list[ChecksumSHA256], sequencing_outcomes_only: bool = False
) -> set[ChecksumSHA256]:
    """
    Given a list of product IDs, returns a potentially empty subset of this list
    as a Set object. Each product, identified by the product ID in the returned
    set, has some QC state associated with it. If `sequencing_outcome_only`
    boolean flag is true, the product must have sequencing QC state associated
    with it; `library` QC state is excluded.

    Arguments:
        `session` - `sqlalchemy.orm.Session`, a connection for LangQC database.
        `ids` - a list of string product IDs.
        `sequencing_outcome_only` - a boolean flag indicating whether the caller
        is interested in `sequencing` QC states only
    """

    query = select(SeqProduct.id_product).where(SeqProduct.id_product.in_(ids))
    if sequencing_outcomes_only is True:
        query = query.join(SeqProduct.qc_state).where(
            QcStateDb.qc_type == _get_qc_type_row(session, SEQUENCING_QC_TYPE)
        )

    # We asked to retrieve data for one column only. The return value for
    # each row is an array with a single value from this column.
    product_ids = [row[0] for row in session.execute(query).all()]

    return set(product_ids)


def get_seq_product(session: Session, id_product: ChecksumSHA256) -> SeqProduct:
    """
    Given a product ID, returns a SeqProduct row for a database entity with
    this product id or None if such entity does not exist.

    Arguments:
        `session` - `sqlalchemy.orm.Session`, a connection for LangQC database.
        `id_product` - a string product ID.
    """
    return (
        session.execute(select(SeqProduct).where(SeqProduct.id_product == id_product))
        .scalars()
        .one_or_none()
    )


def get_qc_state_for_product(
    session: Session, id_product: ChecksumSHA256, qc_type: str = DEFAULT_QC_TYPE
) -> QcStateDb:
    """
    Returns a QcState database row associated with the product with the
    argument product ID. None is returned if either no QC state is associated
    with the product or the product record does not exist.

    An optional `qc_type` argument, which defaults to `sequencing`, defines the
    type of QC state that is returned. If the QC state of this type is not
    available, None is returned.

    Throws `InvalidDictValueError` if the given QC type does not exist in
    the database dictionary of QC types.

    Arguments:
        `session` - `sqlalchemy.orm.Session`, a connection for LangQC database.
        `id_product` - a string product ID.
        `qc_type`- a string QC type.
    """

    qc_type_row = _get_qc_type_row(session, qc_type)
    query = (
        select(QcStateDb)
        .join(QcStateDb.seq_product)
        .where(
            and_(
                SeqProduct.id_product == id_product,
                QcStateDb.qc_type == qc_type_row,
            )
        )
    )
    return session.execute(query).scalars().one_or_none()


def claim_qc_for_product(
    session: Session, seq_product: SeqProduct, user: User
) -> QcStateDb:
    """
    Assigns `Claimed` QC state for the `sequencing` QC type.

    Arguments:
        `session` - `sqlalchemy.orm.Session`, a connection for LangQC database.

        `seq_product` - an existing `lang_qc.db.qc_schema.SeqProduct` object that defines
        the product which will have the `Claimed` QC state assigned.

        `user` - an instance of the existing in the database `lang_qc.db.qc_schema.User`,
        object. The `Claimed` QC state will be associated with this user.
    """

    qc_state = QcStateBasic(
        qc_type=DEFAULT_QC_TYPE,
        qc_state=CLAIMED_QC_STATE,
        is_preliminary=not DEFAULT_FINALITY,
    )
    return assign_qc_state_to_product(session, seq_product, qc_state, user)


def assign_qc_state_to_product(
    session: Session,
    seq_product: SeqProduct,
    qc_state: QcStateBasic,
    user: User,
    application: str = APPLICATION_NAME,
    date_updated: datetime = None,
) -> QcStateDb:
    """
    Creates and persists a new QC state of type specified by `qc_state.qc_type`
    for the product.

    Returns an QcState object representing either new or updated or existing
    row in the `qc_state` table.

    A new row is created if there was no corresponding QC state of the
    matching type in the database.  Changing the `qc_type` value for an
    existing row is not permitted.

    The current row is returned if the current QC state in the database matches
    all attributes of the argument `qc_state` object.

    An updated row is returned in all other cases.

    Records for different types of QC for the same entity can co-exist.
    For example, a sequencing QC record
        (qc_type="sequencing", qc_state="Passed", is_preliminary=true)
    can exist at the same time as a library QC record
        (qc_type="library", qc_state="Passed", is_preliminary=true)
    without conflict. These are outcomes of independent kinds of QC
    assessment.

    A QC state change can be initiated by any user, and any QC state can
    replace any other. Enforcement of business rules must be handled at the
    application level.

    The `InvalidDictValueError` is raised if either the `qc_state` or
    `qc_type` attributes of the `qc_state` object are invalid, i.e. do not
    correspond to any of the database dictionary values.

    The `InconsistentInputError` is raised if the attributes of the `qc_state`
    object contradict each other. The following rules are upheld:
        1. `Claimed` and 'On hold` states can only be preliminary.
        2. The `Claimed` state exists only for `sequencing` QC type.

    For each new or updated record in the `qc_state` table a new record is
    created in the `qc_state_hist` table, thereby preserving a history of all
    changes.

    Arguments:
        `session` - `sqlalchemy.orm.Session`, a connection for LangQC database.

        `seq_product` - an existing `lang_qc.db.qc_schema.SeqProduct` object that defines
        the product which will have the QC state assigned.

        `qc_state` - `QcStateBasic` type object, wraps around attributes of the QC state
        that has to be assigned.

        `user` - an instance of the existing in the database `lang_qc.db.qc_schema.User`,
        object. The new QC state will be associated with this user.

        `application` - a string, the name of the application using this API,
        defaults to `Lang QC`. Used for differentiating between changes via GUI and
        other changes made by scripts or pipelines.

        `date_updated` - an optional `datetime` for recording the timestamp when the
        QC state was changed. Normally the database will set the timestamp, however a
        preset value can be used for backfilling historical data. If a new QC state is
        created, the value of this argument is used for the `date_created` column as well.
    """

    qc_type = qc_state.qc_type
    qc_state_description = qc_state.qc_state
    # The following two function call will validate the request.
    qc_type_row = _get_qc_type_row(session, qc_type)
    qc_state_dict_row = _get_qc_state_dict_row(session, qc_state_description)

    # 'Claimed' and 'On hold' states cannot be final.
    # By enforcing this we simplify rules for assigning QC states
    # to QC flow statuses.
    is_preliminary = 1 if qc_state.is_preliminary is True else 0
    if (is_preliminary == 0) and (qc_state_description in ONLY_PRELIM_STATES):
        raise InconsistentInputError(
            f"QC state '{qc_state_description}' cannot be final"
        )

    # 'Claimed' state is only applicable for 'sequencing' QC type.
    if qc_state_description == CLAIMED_QC_STATE and qc_type != DEFAULT_QC_TYPE:
        raise InconsistentInputError(
            f"QC state '{CLAIMED_QC_STATE}' is incompatible with QC type '{qc_type}'"
        )

    qc_state_db = None
    # Because of the way the unique constraint is set for the qc_state
    # table (see unique_qc_state index), there cannot be more than one
    # record of a given QC type.
    for s in seq_product.qc_state:
        if s.qc_type.qc_type == qc_type:
            qc_state_db = s
            if (
                s.qc_state_dict.state == qc_state_description
                and s.is_preliminary == is_preliminary
            ):
                return s  # No need to update the record.
            qc_state_db = s
            break

    values = {
        "qc_state_dict": qc_state_dict_row,
        "is_preliminary": is_preliminary,
        "user": user,
        "created_by": application,
        "qc_type": qc_type_row,
        "seq_product": seq_product,
    }

    if qc_state_db is not None:
        # Update some of the values of the existing record.
        # No need to update the QC type, it stays the same.
        qc_state_db.qc_state_dict = values["qc_state_dict"]
        qc_state_db.is_preliminary = values["is_preliminary"]
        qc_state_db.user = values["user"]
        qc_state_db.created_by = values["created_by"]
        if date_updated:
            qc_state_db.date_updated = date_updated
    else:
        # Create a new record, date_updated=None is accepted by the ORM as
        # deferring to the schema defaults
        qc_state_db = QcStateDb(
            date_created=date_updated, date_updated=date_updated, **values
        )

    session.add(qc_state_db)
    session.commit()  # This will generate and propagate timestamps.

    qc_state_hist = QcStateHist(
        # Clone timestamps whether from the argument or generated by the DB.
        date_created=qc_state_db.date_created,
        date_updated=qc_state_db.date_updated,
        **values,
    )
    session.add(qc_state_hist)
    session.commit()

    return qc_state_db


def _get_qc_state_by_id_list(
    session: Session, ids: list[ChecksumSHA256], sequencing_outcomes_only: bool
) -> list[QcStateDb]:
    """
    Generates and executes a query for SeqProducts from a list
    of product IDs. Prefetch all related QC states, types, etc.
    """
    query = (
        select(QcStateDb)
        .join(QcStateDb.seq_product)
        .join(QcType)
        .join(QcStateDict)
        .join(User)
        .where(SeqProduct.id_product.in_(ids))
        .options(
            selectinload(QcStateDb.seq_product),
            selectinload(QcStateDb.qc_type),
            selectinload(QcStateDb.user),
            selectinload(QcStateDb.qc_state_dict),
        )
    )
    if sequencing_outcomes_only is True:
        query = query.where(QcType.qc_type == SEQUENCING_QC_TYPE)

    return session.execute(query).scalars().all()


def _get_qc_type_row(session: Session, qc_type: str) -> QcType:

    qc_type_row = None
    try:
        qc_type_row = (
            session.execute(select(QcType).where(QcType.qc_type == qc_type))
            .scalars()
            .one()
        )
    except NoResultFound:
        raise InvalidDictValueError(f"QC type '{qc_type}' is invalid")

    return qc_type_row


def _get_qc_state_dict_row(session: Session, qc_state: str) -> QcStateDict:

    qc_state_dict_row = None
    try:
        qc_state_dict_row = (
            session.execute(select(QcStateDict).where(QcStateDict.state == qc_state))
            .scalars()
            .one()
        )
    except NoResultFound:
        raise InvalidDictValueError(f"QC state '{qc_state}' is invalid")

    return qc_state_dict_row
