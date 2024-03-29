import pytest

from lang_qc.db.helper.qc import (
    get_qc_state_for_product,
    get_qc_states_by_id_product_list,
    product_has_qc_state,
    products_have_qc_state,
    qc_state_dict,
)
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users

MISSING_CHECKSUM = "A" * 64
# "TRACTION_RUN_1", "D1", "On hold", Final
FIRST_GOOD_CHECKSUM = "6657a34aa6159d7e2426f4732a84c51fa2d9186a4578e61ec21de4cb028fc800"
# "TRACTION_RUN_2", "B1", "Failed, Instrument", Preliminary
SECOND_GOOD_CHECKSUM = (
    "e47765a207c810c2c281d5847e18c3015f3753b18bd92e8a2bea1219ba3127ea"
)
# "TRACTION_RUN_16", plate 1
NO_LIB_QC_CHECKSUM = "48056b888e6890a2c2d6020018349167feeb729322b1caff97a28a4a8116d98d"
# "TRACTION_RUN_16", plate 2
NO_SEQ_QC_CHECKSUM = "dc77c4a7f34d84afbb895fcaee72fc8bead9dac20e8d3a9614091d9dd4519acd"

two_good_ids_list = [FIRST_GOOD_CHECKSUM, SECOND_GOOD_CHECKSUM]


def test_bulk_retrieval(qcdb_test_session, load_data4well_retrieval):

    # The test below demonstrates that no run-time type checking of
    # product IDs is performed.
    assert get_qc_states_by_id_product_list(qcdb_test_session, ["dodo"]) == {}

    qc_state_descriptions = ["On hold external", "Failed, Instrument"]

    qc_states = get_qc_states_by_id_product_list(qcdb_test_session, two_good_ids_list)
    assert len(qc_states) == 2
    assert FIRST_GOOD_CHECKSUM in qc_states
    assert SECOND_GOOD_CHECKSUM in qc_states
    list_1 = qc_states[FIRST_GOOD_CHECKSUM]
    list_2 = qc_states[SECOND_GOOD_CHECKSUM]
    for index, l in enumerate([list_1, list_2]):
        assert len(l) == 2
        # The list of QC state objects contains QC states
        # for different QC types.
        assert {o.qc_type for o in l} == {"sequencing", "library"}
        assert {o.qc_state for o in l} == {qc_state_descriptions[index]}

    qc_states = get_qc_states_by_id_product_list(
        session=qcdb_test_session, ids=two_good_ids_list, sequencing_outcomes_only=True
    )
    assert len(qc_states) == 2
    assert FIRST_GOOD_CHECKSUM in qc_states
    assert SECOND_GOOD_CHECKSUM in qc_states
    list_1 = qc_states[FIRST_GOOD_CHECKSUM]
    list_2 = qc_states[SECOND_GOOD_CHECKSUM]
    for index, l in enumerate([list_1, list_2]):
        assert len(l) == 1
        assert l[0].qc_type == "sequencing"
        assert l[0].qc_state == qc_state_descriptions[index]

    qc_states = get_qc_states_by_id_product_list(
        session=qcdb_test_session, ids=[SECOND_GOOD_CHECKSUM, MISSING_CHECKSUM]
    )
    assert len(qc_states) == 1
    assert SECOND_GOOD_CHECKSUM in qc_states
    assert MISSING_CHECKSUM not in qc_states


def test_product_existence(qcdb_test_session, load_data4well_retrieval):

    assert product_has_qc_state(qcdb_test_session, MISSING_CHECKSUM) is False
    for id in two_good_ids_list:
        assert product_has_qc_state(qcdb_test_session, id) is True
        assert product_has_qc_state(qcdb_test_session, id, "sequencing") is True
        assert product_has_qc_state(qcdb_test_session, id, "library") is True

    assert (
        product_has_qc_state(qcdb_test_session, NO_LIB_QC_CHECKSUM, "sequencing")
        is True
    )
    assert (
        product_has_qc_state(qcdb_test_session, NO_LIB_QC_CHECKSUM, "library") is False
    )
    assert product_has_qc_state(qcdb_test_session, NO_LIB_QC_CHECKSUM) is True

    assert (
        product_has_qc_state(qcdb_test_session, NO_SEQ_QC_CHECKSUM, "sequencing")
        is False
    )
    assert (
        product_has_qc_state(qcdb_test_session, NO_SEQ_QC_CHECKSUM, "library") is True
    )
    assert product_has_qc_state(qcdb_test_session, NO_SEQ_QC_CHECKSUM) is True

    with pytest.raises(Exception, match=r"QC type 'some_type' is invalid"):
        product_has_qc_state(qcdb_test_session, NO_SEQ_QC_CHECKSUM, "some_type")


def test_products_existence(qcdb_test_session, load_data4well_retrieval):

    ids = [
        FIRST_GOOD_CHECKSUM,
        SECOND_GOOD_CHECKSUM,
        NO_LIB_QC_CHECKSUM,
        NO_SEQ_QC_CHECKSUM,
    ]

    assert products_have_qc_state(qcdb_test_session, [MISSING_CHECKSUM]) == set()
    assert products_have_qc_state(qcdb_test_session, [FIRST_GOOD_CHECKSUM]) == set(
        [FIRST_GOOD_CHECKSUM]
    )
    assert products_have_qc_state(
        qcdb_test_session, [MISSING_CHECKSUM, FIRST_GOOD_CHECKSUM]
    ) == set([FIRST_GOOD_CHECKSUM])
    assert products_have_qc_state(qcdb_test_session, ids) == set(ids)

    assert (
        products_have_qc_state(
            qcdb_test_session, [MISSING_CHECKSUM, NO_SEQ_QC_CHECKSUM], True
        )
        == set()
    )
    assert products_have_qc_state(qcdb_test_session, ids, True) == set(
        [FIRST_GOOD_CHECKSUM, SECOND_GOOD_CHECKSUM, NO_LIB_QC_CHECKSUM]
    )


def test_product_qc_state_retrieval(qcdb_test_session, load_data4well_retrieval):

    assert get_qc_state_for_product(qcdb_test_session, MISSING_CHECKSUM) is None

    with pytest.raises(Exception, match=r"QC type 'some_type' is invalid"):
        get_qc_state_for_product(
            session=qcdb_test_session,
            id_product=SECOND_GOOD_CHECKSUM,
            qc_type="some_type",
        )

    qc_state = get_qc_state_for_product(qcdb_test_session, FIRST_GOOD_CHECKSUM)
    assert qc_state is not None
    assert qc_state.seq_product.id_product == FIRST_GOOD_CHECKSUM
    assert qc_state.qc_type.qc_type == "sequencing"
    assert qc_state.qc_state_dict.state == "On hold external"

    qc_state = get_qc_state_for_product(
        session=qcdb_test_session, id_product=FIRST_GOOD_CHECKSUM, qc_type="sequencing"
    )
    assert qc_state is not None
    assert qc_state.seq_product.id_product == FIRST_GOOD_CHECKSUM
    assert qc_state.qc_type.qc_type == "sequencing"
    assert qc_state.qc_state_dict.state == "On hold external"

    qc_state = get_qc_state_for_product(
        session=qcdb_test_session, id_product=FIRST_GOOD_CHECKSUM, qc_type="library"
    )
    assert qc_state is not None
    assert qc_state.seq_product.id_product == FIRST_GOOD_CHECKSUM
    assert qc_state.qc_type.qc_type == "library"
    assert qc_state.qc_state_dict.state == "On hold external"

    qc_state = get_qc_state_for_product(qcdb_test_session, SECOND_GOOD_CHECKSUM)
    assert qc_state is not None
    assert qc_state.seq_product.id_product == SECOND_GOOD_CHECKSUM
    assert qc_state.qc_type.qc_type == "sequencing"
    assert qc_state.qc_state_dict.state == "Failed, Instrument"

    qc_state = get_qc_state_for_product(
        session=qcdb_test_session, id_product=SECOND_GOOD_CHECKSUM, qc_type="library"
    )
    assert qc_state is not None
    assert qc_state.seq_product.id_product == SECOND_GOOD_CHECKSUM
    assert qc_state.qc_type.qc_type == "library"
    assert qc_state.qc_state_dict.state == "Failed, Instrument"


def test_dict_helper(qcdb_test_session, load_dicts_and_users):

    expected_sorted_states = [
        "Passed",
        "Aborted",
        "Failed",
        "Failed, Instrument",
        "Failed, SMRT cell",
        "Claimed",
        "On hold",
        "On hold external",
        "Undecided",
    ]
    assert list(qc_state_dict(qcdb_test_session).keys()) == expected_sorted_states
