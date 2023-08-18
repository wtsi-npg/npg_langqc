from datetime import datetime

import pytest
from npg_id_generation.pac_bio import PacBioEntity
from sqlalchemy import select

from lang_qc.db.helper.qc import assign_qc_state_to_product, claim_qc_for_product
from lang_qc.db.qc_schema import QcState, QcStateHist, SeqProduct, User
from lang_qc.models.qc_state import QcStateBasic
from lang_qc.util.errors import InconsistentInputError
from tests.fixtures.well_data import (
    load_data4qc_assign,
    load_data4well_retrieval,
    load_dicts_and_users,
)

time_now = datetime.now()


def test_claim_qc(qcdb_test_session, load_data4well_retrieval, load_data4qc_assign):

    users = qcdb_test_session.execute(select(User)).scalars().all()
    user1 = users[0]
    user2 = users[1]

    id = PacBioEntity(
        run_name="TRACTION_RUN_2", well_label="A1", plate_number=2
    ).hash_product_id()
    seq_product = qcdb_test_session.execute(
        select(SeqProduct).where(SeqProduct.id_product == id)
    ).scalar_one()

    state_obj = claim_qc_for_product(
        session=qcdb_test_session, seq_product=seq_product, user=user1
    )
    assert state_obj.date_created == state_obj.date_updated
    assert state_obj.user == user1
    assert state_obj.qc_type.qc_type == "sequencing"
    assert state_obj.qc_state_dict.state == "Claimed"
    assert state_obj.created_by == "LangQC"
    assert state_obj.is_preliminary == 1
    assert state_obj.seq_product.id_product == id
    id_seq_product = state_obj.id_seq_product
    hist_objs = _hist_objects(qcdb_test_session, id_seq_product)
    assert len(hist_objs) == 1
    _test_hist_object(state_obj, hist_objs[0])

    # New QC state record is not created
    state_obj = claim_qc_for_product(
        session=qcdb_test_session, seq_product=seq_product, user=user2
    )
    assert state_obj.date_created == state_obj.date_updated
    assert state_obj.user == user1
    assert state_obj.qc_type.qc_type == "sequencing"
    assert state_obj.qc_state_dict.state == "Claimed"
    assert state_obj.created_by == "LangQC"
    assert state_obj.is_preliminary == 1
    assert state_obj.seq_product.id_product == id
    assert state_obj.id_seq_product == id_seq_product
    hist_objs = _hist_objects(qcdb_test_session, id_seq_product)
    assert len(hist_objs) == 1


def test_assign_qc_success(
    qcdb_test_session, load_data4well_retrieval, load_data4qc_assign
):

    # The same well as claimed above.
    id = PacBioEntity(
        run_name="TRACTION_RUN_2", well_label="A1", plate_number=2
    ).hash_product_id()

    users = qcdb_test_session.execute(select(User)).scalars().all()
    user2 = users[1]
    seq_product = qcdb_test_session.execute(
        select(SeqProduct).where(SeqProduct.id_product == id)
    ).scalar_one()
    id_seq_product = seq_product.id_seq_product
    # In case oly this test is run, claim.
    claim_qc_for_product(session=qcdb_test_session, seq_product=seq_product, user=user2)

    new_state = QcStateBasic(
        qc_state="Passed", qc_type="sequencing", is_preliminary=True
    )
    args = {
        "seq_product": seq_product,
        "user": user2,
        "qc_state": new_state,
        "application": "MyScript",
    }
    state_obj = assign_qc_state_to_product(session=qcdb_test_session, **args)
    assert _num_qc_state_objects(qcdb_test_session, id_seq_product) == 1
    assert state_obj.user == user2
    assert state_obj.qc_type.qc_type == "sequencing"
    assert state_obj.qc_state_dict.state == "Passed"
    assert state_obj.created_by == "MyScript"
    assert state_obj.is_preliminary == 1
    assert state_obj.seq_product.id_product == id
    hist_objs = _hist_objects(qcdb_test_session, id_seq_product)
    assert len(hist_objs) == 2
    _test_hist_object(state_obj, hist_objs[1])

    # Expect no update despite a different user
    args["user"] = users[0]
    state_obj_the_same = assign_qc_state_to_product(qcdb_test_session, **args)
    assert state_obj == state_obj_the_same
    hist_objs = _hist_objects(qcdb_test_session, id_seq_product)
    assert len(hist_objs) == 2

    # Expect a new QC state for a different QC type
    new_state = QcStateBasic(qc_state="Failed", qc_type="library", is_preliminary=False)
    args["qc_state"] = new_state
    state_obj = assign_qc_state_to_product(session=qcdb_test_session, **args)
    assert state_obj.qc_type.qc_type == "library"
    assert state_obj.is_preliminary == 0
    assert state_obj.qc_state_dict.state == "Failed"
    assert _num_qc_state_objects(qcdb_test_session, id_seq_product) == 2
    hist_objs = _hist_objects(qcdb_test_session, id_seq_product)
    assert len(hist_objs) == 3
    _test_hist_object(state_obj, hist_objs[2])

    # Test setting time explicitly on update
    new_state = QcStateBasic(qc_state="Failed", qc_type="library", is_preliminary=True)
    args["qc_state"] = new_state
    past_date = datetime(year=2021, month=4, day=7, hour=11, minute=56, second=6)
    args["date_updated"] = past_date

    state_obj = assign_qc_state_to_product(session=qcdb_test_session, **args)
    date_updated = state_obj.date_updated
    assert date_updated.year == past_date.year
    assert date_updated.month == past_date.month
    assert date_updated.day == past_date.day
    assert date_updated.hour == past_date.hour
    assert date_updated.minute == past_date.minute
    assert date_updated.second == past_date.second
    assert state_obj.date_created.year == time_now.year

    # Test setting time explicitly on creating a new record.
    id = PacBioEntity(
        run_name="TRACTION_RUN_2", well_label="B1", plate_number=2
    ).hash_product_id()
    seq_product = qcdb_test_session.execute(
        select(SeqProduct).where(SeqProduct.id_product == id)
    ).scalar_one()
    args["seq_product"] = seq_product
    state_obj = assign_qc_state_to_product(session=qcdb_test_session, **args)
    date_updated = state_obj.date_updated
    assert date_updated.year == past_date.year
    assert date_updated.month == past_date.month
    assert date_updated.day == past_date.day
    assert date_updated.hour == past_date.hour
    assert date_updated.minute == past_date.minute
    assert date_updated.second == past_date.second
    date_created = state_obj.date_updated
    assert date_created.year == past_date.year
    assert date_created.month == past_date.month
    assert date_created.day == past_date.day
    assert date_created.hour == past_date.hour
    assert date_created.minute == past_date.minute
    assert date_created.second == past_date.second


def test_assign_qc_errors(
    qcdb_test_session, load_data4well_retrieval, load_data4qc_assign
):

    id = PacBioEntity(
        run_name="TRACTION_RUN_2", well_label="A1", plate_number=2
    ).hash_product_id()

    users = qcdb_test_session.execute(select(User)).scalars().all()
    seq_product = qcdb_test_session.execute(
        select(SeqProduct).where(SeqProduct.id_product == id)
    ).scalar_one()

    new_state = QcStateBasic(
        qc_state="Claimed", qc_type="sequencing", is_preliminary=False
    )
    args = {"seq_product": seq_product, "user": users[1], "qc_state": new_state}
    with pytest.raises(
        InconsistentInputError, match=r"QC state 'Claimed' cannot be final"
    ):
        assign_qc_state_to_product(session=qcdb_test_session, **args)

    new_state = QcStateBasic(qc_state="Claimed", qc_type="library", is_preliminary=True)
    args["qc_state"] = new_state
    with pytest.raises(
        InconsistentInputError,
        match=r"QC state 'Claimed' is incompatible with QC type 'library'",
    ):
        assign_qc_state_to_product(session=qcdb_test_session, **args)

    new_state = QcStateBasic(
        qc_state="On hold", qc_type="sequencing", is_preliminary=False
    )
    args["qc_state"] = new_state
    with pytest.raises(
        InconsistentInputError, match=r"QC state 'On hold' cannot be final"
    ):
        assign_qc_state_to_product(session=qcdb_test_session, **args)


def _test_hist_object(state_obj, hist_obj):

    assert state_obj.date_created == hist_obj.date_created
    assert state_obj.date_updated == hist_obj.date_updated
    assert state_obj.id_user == hist_obj.id_user
    assert state_obj.id_qc_type == hist_obj.id_qc_type
    assert state_obj.id_qc_state_dict == hist_obj.id_qc_state_dict
    assert state_obj.created_by == hist_obj.created_by
    assert state_obj.is_preliminary == hist_obj.is_preliminary


def _num_qc_state_objects(session, id_seq_product):

    objs = (
        session.execute(
            select(QcState).filter(QcState.id_seq_product == id_seq_product)
        )
        .scalars()
        .all()
    )
    return len(objs)


def _hist_objects(session, id_seq_product):

    return (
        session.execute(
            select(QcStateHist).filter(QcStateHist.id_seq_product == id_seq_product)
        )
        .scalars()
        .all()
    )
