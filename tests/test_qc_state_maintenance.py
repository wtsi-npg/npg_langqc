from datetime import datetime

import pytest
from npg_id_generation.pac_bio import PacBioEntity
from sqlalchemy import select

from lang_qc.db.helper.well import (
    InconsistentInputError,
    InvalidDictValueError,
    QcDictDB,
    WellQc,
)
from lang_qc.db.mlwh_schema import PacBioRunWellMetrics
from lang_qc.db.qc_schema import QcState, QcStateHist, User
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_dict_helper(qcdb_test_session, load_dicts_and_users):

    helper = QcDictDB(session=qcdb_test_session)

    for type in ("library", "sequencing"):
        library_row = helper.qc_type_dict_row(type)
        assert library_row.qc_type == type

    with pytest.raises(InvalidDictValueError, match=r"QC type 'plate' is invalid"):
        helper.qc_type_dict_row("plate")

    for state_name in ("Passed", "Undecided", "Aborted"):
        dict_row = helper.qc_state_dict_row(state_name)
        assert dict_row.state == state_name

    with pytest.raises(InvalidDictValueError, match=r"QC state 'full' is invalid"):
        helper.qc_state_dict_row("full")

    expected_sorted_states = [
        "Passed",
        "Aborted",
        "Failed",
        "Failed, Instrument",
        "Failed, SMRT cell",
        "Claimed",
        "On hold",
        "Undecided",
    ]
    assert list(helper.qc_states.keys()) == expected_sorted_states


def test_well_state_helper(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

    session = qcdb_test_session
    users = session.execute(select(User)).scalars().all()
    user1 = users[0].username
    user2 = users[1].username

    pbi = PacBioEntity(run_name="TRACTION_RUN_2", well_label="A1", plate_number=2)
    id = pbi.hash_product_id()
    json = pbi.json()
    time_now = datetime.now()
    mlwh_well = mlwhdb_test_session.execute(
        select(PacBioRunWellMetrics).where(
            PacBioRunWellMetrics.id_pac_bio_product == id,
        )
    ).scalar_one_or_none()

    helper = WellQc(session=session)

    assert helper.current_qc_state(id) is None

    # Expect a new QC state and product record are created
    state_obj = helper.assign_qc_state(
        mlwh_well=mlwh_well, user=users[0], qc_state="Claimed"
    )
    assert state_obj.date_created == state_obj.date_updated
    assert state_obj.user.username == user1
    assert state_obj.qc_type.qc_type == "sequencing"
    assert state_obj.qc_state_dict.state == "Claimed"
    assert state_obj.created_by == "LangQC"
    assert state_obj.is_preliminary == 1

    assert state_obj.seq_product.seq_platform.name == "PacBio"
    assert state_obj.seq_product.id_product == id
    assert len(state_obj.seq_product.sub_products) == 1
    sub_product = state_obj.seq_product.sub_products[0]
    assert sub_product.properties == json
    assert sub_product.properties_digest == id
    assert sub_product.value_attr_one == "TRACTION_RUN_2"
    assert sub_product.value_attr_two == "A1"
    assert sub_product.value_attr_three == "2"  # A string!

    id_seq_product = state_obj.id_seq_product
    hist_objs = _hist_objects(session, id_seq_product)
    assert len(hist_objs) == 1
    _test_hist_object(state_obj, hist_objs[0])

    # Current QC state is defined now
    current_qc_state = helper.current_qc_state(id)
    assert current_qc_state == state_obj
    # ... but not for a library
    assert helper.current_qc_state(id, "library") is None
    # Check that the date is very recent
    delta = current_qc_state.date_created - time_now
    assert delta.total_seconds() <= 1

    args = {
        "mlwh_well": mlwh_well,
        "user": users[1],
        "qc_state": "Passed",
        "qc_type": "sequencing",
        "is_preliminary": True,
        "application": "MyScript",
    }

    state_obj = helper.assign_qc_state(**args)
    assert _num_qc_state_objects(session, id_seq_product) == 1
    assert state_obj.user.username == user2
    assert state_obj.qc_type.qc_type == args["qc_type"]
    assert state_obj.qc_state_dict.state == args["qc_state"]
    assert state_obj.created_by == args["application"]
    assert state_obj.is_preliminary == 1
    assert state_obj.id_seq_product == id_seq_product
    hist_objs = _hist_objects(session, id_seq_product)
    assert len(hist_objs) == 2
    _test_hist_object(state_obj, hist_objs[1])

    # Expect no update despite a different user
    args["user"] = users[0]
    state_obj_the_same = helper.assign_qc_state(**args)
    assert state_obj == state_obj_the_same
    assert _num_qc_state_objects(session, id_seq_product) == 1
    hist_objs = _hist_objects(session, id_seq_product)
    assert len(hist_objs) == 2

    # Expect a new QC state for a different QC type
    args["qc_type"] = "library"
    state_obj = helper.assign_qc_state(**args)
    assert state_obj.qc_type.qc_type == args["qc_type"]
    assert _num_qc_state_objects(session, id_seq_product) == 2
    hist_objs = _hist_objects(session, id_seq_product)
    assert len(hist_objs) == 3
    _test_hist_object(state_obj, hist_objs[2])

    # Current QC state is defined for library QC
    assert helper.current_qc_state(id, "library") == state_obj
    # ... and is different from the current QC state for sequencing
    assert helper.current_qc_state(id, "sequencing") != state_obj

    args["is_preliminary"] = False
    state_obj = helper.assign_qc_state(**args)
    assert state_obj.is_preliminary == 0
    hist_objs = _hist_objects(session, id_seq_product)
    assert len(hist_objs) == 4
    _test_hist_object(state_obj, hist_objs[3])

    args = {
        "mlwh_well": mlwh_well,
        "user": users[1],
        "qc_state": "Claimed",
        "qc_type": "sequencing",
        "is_preliminary": False,
        "application": "MyScript",
    }
    with pytest.raises(
        InconsistentInputError, match=r"QC state 'Claimed' cannot be final"
    ):
        helper.assign_qc_state(**args)
    args["qc_state"] = "On hold"
    with pytest.raises(
        InconsistentInputError, match=r"QC state 'On hold' cannot be final"
    ):
        helper.assign_qc_state(**args)

    # Test setting time explicitly on update
    past_date = datetime(year=2021, month=4, day=7, hour=11, minute=56, second=6)
    args["is_preliminary"] = "True"
    args["date_updated"] = past_date
    state_obj = helper.assign_qc_state(**args)
    date_updated = state_obj.date_updated
    assert date_updated.year == past_date.year
    assert date_updated.month == past_date.month
    assert date_updated.day == past_date.day
    assert date_updated.hour == past_date.hour
    assert date_updated.minute == past_date.minute
    assert date_updated.second == past_date.second
    assert state_obj.date_created.year == time_now.year

    # ... and on creating a new record.
    pbi = PacBioEntity(run_name="TRACTION_RUN_2", well_label="B1", plate_number=2)
    id = pbi.hash_product_id()
    mlwh_well = mlwhdb_test_session.execute(
        select(PacBioRunWellMetrics).where(
            PacBioRunWellMetrics.id_pac_bio_product == id,
        )
    ).scalar_one_or_none()
    args["mlwh_well"] = mlwh_well

    helper = WellQc(session=session)
    state_obj = helper.assign_qc_state(**args)
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

    hist_objs = (
        session.execute(
            select(QcStateHist).filter(QcStateHist.id_seq_product == id_seq_product)
        )
        .scalars()
        .all()
    )
    return hist_objs
