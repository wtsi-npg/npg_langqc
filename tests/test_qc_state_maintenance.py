import pytest
from npg_id_generation.pac_bio import PacBioEntity
from sqlalchemy import select

from lang_qc.db.helper.well import InvalidDictValueError, QcDictDB, WellQc
from lang_qc.db.qc_schema import QcState, QcStateHist, User
from tests.fixtures.qc_db_basic_data import load_dicts_and_users


def test_dict_helper(load_dicts_and_users):

    session = load_dicts_and_users

    helper = QcDictDB(session=session)

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


def test_well_state_helper(load_dicts_and_users):

    session = load_dicts_and_users
    users = session.execute(select(User)).scalars().all()
    user1 = users[0].username
    user2 = users[1].username

    pbi = PacBioEntity(run_name="Run 1", well_label="A")
    id = pbi.hash_product_id()
    json = pbi.json()

    helper = WellQc(session=session, run_name="Run 1", well_label="A")

    assert helper.current_qc_state() is None

    # Expect a new QC state and product record are created
    state_obj = helper.assign_qc_state(user=users[0], qc_state="Claimed")
    assert state_obj.date_created == state_obj.date_updated
    assert state_obj.user.username == user1
    assert state_obj.qc_type.qc_type == "sequencing"
    assert state_obj.qc_state_dict.state == "Claimed"
    assert state_obj.created_by == "LangQC"
    assert state_obj.is_preliminary == 1

    assert state_obj.seq_product.seq_platform.name == "PacBio"
    assert state_obj.seq_product.id_product == id
    assert len(state_obj.seq_product.product_layout) == 1
    sub_product = state_obj.seq_product.product_layout[0].sub_product
    assert sub_product.properties == json
    assert sub_product.properties_digest == id
    assert sub_product.value_attr_one == "Run 1"
    assert sub_product.value_attr_two == "A"

    id_seq_product = state_obj.id_seq_product
    hist_objs = _hist_objects(session, id_seq_product)
    assert len(hist_objs) == 1
    _test_hist_object(state_obj, hist_objs[0])

    # Current QC state is defined now
    assert helper.current_qc_state() == state_obj
    # ... but not for a library
    assert helper.current_qc_state("library") is None

    args = {
        "user": users[1],
        "qc_state": "Passed",
        "qc_type": "sequencing",
        "is_preliminary": True,
        "application": "MyScript",
    }

    state_obj = helper.assign_qc_state(**args)
    assert _num_qc_state_objects(session, id_seq_product) == 1
    assert state_obj.user.username == user2
    assert state_obj.qc_type.qc_type == "sequencing"
    assert state_obj.qc_state_dict.state == "Passed"
    assert state_obj.created_by == "MyScript"
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
    assert state_obj.qc_type.qc_type == "library"
    assert _num_qc_state_objects(session, id_seq_product) == 2
    hist_objs = _hist_objects(session, id_seq_product)
    assert len(hist_objs) == 3
    _test_hist_object(state_obj, hist_objs[2])

    # Current QC state is defined for library QC
    assert helper.current_qc_state("library") == state_obj
    # ... and is different from the current QC state for sequencing
    assert helper.current_qc_state("sequencing") != state_obj

    args["is_preliminary"] = False
    state_obj = helper.assign_qc_state(**args)
    assert state_obj.is_preliminary == 0
    hist_objs = _hist_objects(session, id_seq_product)
    assert len(hist_objs) == 4
    _test_hist_object(state_obj, hist_objs[3])


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
