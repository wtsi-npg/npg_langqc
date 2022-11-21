import pytest
from npg_id_generation.pac_bio import PacBioEntity

from lang_qc.db.helper.well import InvalidDictValueError, QcDictDB
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
