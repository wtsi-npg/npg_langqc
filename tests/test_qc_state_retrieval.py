from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from lang_qc.db.helper.qc import (
    get_qc_state_for_product,
    get_qc_states,
    get_qc_states_by_id_product_list,
    product_has_qc_state,
    products_have_qc_state,
    qc_state_dict,
)
from lang_qc.db.qc_schema import QcState
from lang_qc.models.qc_state import QcState as QcStateModel
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


def test_bulk_retrieval_by_id(qcdb_test_session, load_data4well_retrieval):

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


def test_bulk_retrieval(qcdb_test_session, load_data4well_retrieval):

    with pytest.raises(ValueError, match=r"num_weeks should be a positive number"):
        assert get_qc_states(qcdb_test_session, num_weeks=-1)

    qc_states = (
        qcdb_test_session.execute(select(QcState).order_by(QcState.date_updated.desc()))
        .scalars()
        .all()
    )
    now = datetime.today()
    max_interval = now - qc_states[-1].date_updated
    max_num_weeks = int(max_interval.days / 7 + 1)
    min_interval = now - qc_states[0].date_updated
    min_num_weeks = int(min_interval.days / 7 - 1)

    assert min_num_weeks > 2
    # Set the look-back number of weeks to the period with no records.
    qc_states_dict = get_qc_states(qcdb_test_session, num_weeks=(min_num_weeks - 1))
    assert len(qc_states_dict) == 0

    # Retrieve all available QC states.
    qc_states_dict = get_qc_states(qcdb_test_session, num_weeks=max_num_weeks)
    # Test total number of QcState objects.
    assert sum([len(l) for l in qc_states_dict.values()]) == len(qc_states)
    # Test number of items in the dictionary.
    assert len(qc_states_dict) == len(
        {qc_state.id_seq_product: 1 for qc_state in qc_states}
    )

    # Retrieve all available final QC states.
    qc_states_dict = get_qc_states(
        qcdb_test_session, num_weeks=max_num_weeks, final_only=True
    )
    assert sum([len(l) for l in qc_states_dict.values()]) == len(
        [qc_state for qc_state in qc_states if qc_state.is_preliminary == 0]
    )
    assert {id: len(l) for (id, l) in qc_states_dict.items()} == {
        "e47765a207c810c2c281d5847e18c3015f3753b18bd92e8a2bea1219ba3127ea": 2,
        "977089cd272dffa70c808d74159981c0d1363840875452a868a4c5e15f1b2072": 2,
        "dc99ab8cb6762df5c935adaeb1f0c49ff34af96b6fa3ebf9a90443079c389579": 2,
        "5e91b9246b30c2df4e9f2a2313ce097e93493b0a822e9d9338e32df5d58db585": 2,
    }

    # Retrieve all available sequencing type QC states.
    qc_states_dict = get_qc_states(
        qcdb_test_session, num_weeks=max_num_weeks, sequencing_outcomes_only=True
    )
    assert len(qc_states_dict) == len(
        [qc_state for qc_state in qc_states if qc_state.qc_type.qc_type == "sequencing"]
    )

    # Retrieve all available sequencing type final QC states.
    qc_states_dict = get_qc_states(
        qcdb_test_session,
        num_weeks=max_num_weeks,
        final_only=True,
        sequencing_outcomes_only=True,
    )
    assert len(qc_states_dict) == len(
        [
            qc_state
            for qc_state in qc_states
            if (
                qc_state.is_preliminary == 0
                and qc_state.qc_type.qc_type == "sequencing"
            )
        ]
    )
    assert {id: len(l) for (id, l) in qc_states_dict.items()} == {
        "e47765a207c810c2c281d5847e18c3015f3753b18bd92e8a2bea1219ba3127ea": 1,
        "977089cd272dffa70c808d74159981c0d1363840875452a868a4c5e15f1b2072": 1,
        "dc99ab8cb6762df5c935adaeb1f0c49ff34af96b6fa3ebf9a90443079c389579": 1,
        "5e91b9246b30c2df4e9f2a2313ce097e93493b0a822e9d9338e32df5d58db585": 1,
    }

    # Retrieve recent sequencing type final QC states.
    num_weeks = max_num_weeks - 44
    qc_states_dict = get_qc_states(
        qcdb_test_session,
        num_weeks=num_weeks,
        final_only=True,
        sequencing_outcomes_only=True,
    )
    earliest_time = now - timedelta(weeks=num_weeks)
    assert len(qc_states_dict) == len(
        [
            qc_state
            for qc_state in qc_states
            if (
                qc_state.date_updated > earliest_time
                and qc_state.is_preliminary == 0
                and qc_state.qc_type.qc_type == "sequencing"
            )
        ]
    )
    product_id = "5e91b9246b30c2df4e9f2a2313ce097e93493b0a822e9d9338e32df5d58db585"
    assert {id: len(l) for (id, l) in qc_states_dict.items()} == {product_id: 1}
    qc_state = qc_states_dict[product_id][0]
    assert isinstance(qc_state, QcStateModel)
    assert qc_state.id_product == product_id
    assert qc_state.is_preliminary is False
    assert qc_state.qc_type == "sequencing"


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
