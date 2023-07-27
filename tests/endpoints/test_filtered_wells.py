from fastapi.testclient import TestClient

from tests.fixtures.inbox_data import inbox_data
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_incorrect_filter(test_client: TestClient):
    """Expect a 422 response when an incorrect filter is given."""

    response = test_client.get(
        "/pacbio/wells?page_size=1&page_number=1&qc_status=thisdoesntexist"
    )
    assert response.status_code == 422

    response = test_client.get("/pacbio/wells?page_size=1&page_number=-1")
    assert response.status_code == 422  # positive value is expected
    response = test_client.get("/pacbio/wells?page_size=-11&page_number=1")
    assert response.status_code == 422  # positive value is expected

    response = test_client.get("/pacbio/wells")
    assert response.status_code == 422  # page size and number should be given

    response = test_client.get("/pacbio/wells?page_number=1")
    assert response.status_code == 422  # page size should be given

    response = test_client.get("/pacbio/wells?page_size=1")
    assert response.status_code == 422  # page number should be given


def test_qc_complete_filter(test_client: TestClient, load_data4well_retrieval):
    """Test passing `qc_complete` filter."""

    status = "qc_complete"
    expected_data = [
        {"TRACTION_RUN_2:D1": "Failed, SMRT cell"},
        {"TRACTION_RUN_2:B1": "Failed, Instrument"},
        {"TRACTION_RUN_4:B1": "Failed"},
        {"TRACTION_RUN_5:B1": "Passed"},
    ]
    expected_data.reverse()
    num_total = len(expected_data)

    response = test_client.get(
        "/pacbio/wells?page_size=10&page_number=1&qc_status=" + status
    )
    _assert_filtered_results(response, expected_data, 10, 1, num_total)
    for well in response.json()["wells"]:
        assert well["run_start_time"] is not None
        assert well["run_complete_time"] is not None
        assert well["well_start_time"] is not None
        assert well["well_complete_time"] is not None
        if well["run_name"] == "TRACTION_RUN_5":
            assert well["instrument_name"] == "64016E"
            assert well["instrument_type"] == "Sequel2e"
        else:
            assert well["instrument_type"] == "Revio"
            if well["run_name"] == "TRACTION_RUN_2":
                assert well["instrument_name"] == "12345"
            else:
                assert well["instrument_name"] == "1234"

    response = test_client.get(
        "/pacbio/wells?page_size=10&page_number=2&qc_status=" + status
    )
    _assert_filtered_results(response, [], 10, 2, num_total)

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=1&qc_status=" + status
    )
    ed = expected_data[0:2]
    _assert_filtered_results(response, ed, 2, 1, num_total)

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=2&qc_status=" + status
    )
    ed = expected_data[2:]
    _assert_filtered_results(response, ed, 2, 2, num_total)


def test_on_hold_filter(test_client: TestClient, load_data4well_retrieval):
    """Test passing `on_hold` filter."""

    status = "on_hold"
    expected_data = [
        {"TRACTION_RUN_1:D1": "On hold"},
        {"TRACTION_RUN_1:B1": "On hold"},
    ]
    num_total = len(expected_data)

    response = test_client.get(
        "/pacbio/wells?page_size=10&page_number=1&qc_status=" + status
    )
    _assert_filtered_results(response, expected_data, 10, 1, num_total)

    response = test_client.get(
        "/pacbio/wells?page_size=10&page_number=2&qc_status=" + status
    )
    assert response.json()["wells"] == []  # empty page

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=1&qc_status=" + status
    )
    ed = expected_data[0:2]
    _assert_filtered_results(response, ed, 2, 1, num_total)


def test_in_progress_filter(test_client: TestClient, load_data4well_retrieval):
    """Test passing `in_progress` filter."""

    expected_data = [
        {"TRACTION_RUN_5:A1": "Passed"},
        {"TRACTION_RUN_6:A1": "Aborted"},
        {"TRACTION_RUN_6:B1": "Aborted"},
        {"TRACTION_RUN_4:A1": "Failed"},
        {"TRACTION_RUN_2:C1": "Failed, SMRT cell"},
        {"TRACTION_RUN_1:C1": "Claimed"},
        {"TRACTION_RUN_2:A1": "Failed, Instrument"},
        {"TRACTION_RUN_1:E1": "Claimed"},
        {"TRACTION_RUN_1:A1": "Claimed"},
        {"TRACTION_RUN_7:A1": "Failed"},
    ]
    num_total = len(expected_data)

    response = test_client.get(
        "/pacbio/wells?qc_status=in_progress&page_size=5&page_number=1"
    )
    _assert_filtered_results(response, expected_data[:5], 5, 1, num_total)

    response = test_client.get(
        "/pacbio/wells?qc_status=in_progress&page_size=5&page_number=2"
    )
    _assert_filtered_results(response, expected_data[5:], 5, 2, num_total)


def test_inbox_filter(test_client: TestClient, load_data4well_retrieval):
    """Test passing `inbox` filter."""

    status = "inbox"

    expected_data = [
        {"TRACTION_RUN_4:C1": None},
        {"TRACTION_RUN_4:D1": None},
        {"TRACTION_RUN_3:A1": None},
        {"TRACTION_RUN_3:B1": None},
        {"TRACTION_RUN_10:A1": None},
        {"TRACTION_RUN_10:B1": None},
        {"TRACTION_RUN_10:C1": None},
        {"TRACTION_RUN_12:A1": None},
    ]
    num_total = len(expected_data)

    response = test_client.get("/pacbio/wells?page_size=100&page_number=1")
    _assert_filtered_results(response, expected_data, 100, 1, num_total)

    response = test_client.get(
        "/pacbio/wells?qc_status=inbox&page_size=100&page_number=1"
    )
    _assert_filtered_results(response, expected_data, 100, 1, num_total)

    response = test_client.get(
        "/pacbio/wells?page_size=100&page_number=2&qc_status=inbox"
    )
    assert response.json()["wells"] == []  # empty page

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=1&qc_status=inbox"
    )
    ed = expected_data[0:2]
    _assert_filtered_results(response, ed, 2, 1, num_total)

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=2&qc_status=inbox"
    )
    ed = expected_data[2:4]
    _assert_filtered_results(response, ed, 2, 2, num_total)

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=4&qc_status=inbox"
    )
    ed = expected_data[6:]
    _assert_filtered_results(response, ed, 2, 4, num_total)

    response = test_client.get(
        "/pacbio/wells?page_size=3&page_number=2&qc_status=inbox"
    )
    ed = expected_data[3:6]
    _assert_filtered_results(response, ed, 3, 2, num_total)

    response = test_client.get(
        "/pacbio/wells?page_size=3&page_number=3&qc_status=inbox"
    )
    ed = expected_data[6:]
    _assert_filtered_results(response, ed, 3, 3, num_total)


def test_unknown_filter(test_client: TestClient, load_data4well_retrieval):
    """Test passing `unknown` filter."""

    expected_data = [
        {"SUBTRACTION_RUN_15:A1": None},
        {"TRACTION_RUN_14:B1": None},
    ]
    num_total = len(expected_data)

    response = test_client.get(
        "/pacbio/wells?qc_status=unknown&page_size=5&page_number=1"
    )
    _assert_filtered_results(response, expected_data, 5, 1, num_total)

    response = test_client.get(
        "/pacbio/wells?qc_status=unknown&page_size=1&page_number=2"
    )
    _assert_filtered_results(response, expected_data[1:], 1, 2, num_total)

    response = test_client.get(
        "/pacbio/wells?qc_status=unknown&page_size=1&page_number=4"
    )
    _assert_filtered_results(response, [], 1, 4, num_total)


def test_aborted_filter(test_client: TestClient, load_data4well_retrieval):
    """Test passing `aborted` filter."""

    expected_data = [
        {"TRACTION_RUN_15:A1": None},
        {"TRACTION_RUN_15:B1": None},
        {"TRACTION_RUN_15:C1": None},
        {"TRACTION_RUN_15:D1": None},
        {"TRACTION_RUN_7:A1": "Failed"},
        {"TRACTION_RUN_9:A1": None},
    ]
    num_total = len(expected_data)

    response = test_client.get(
        "/pacbio/wells?qc_status=aborted&page_size=6&page_number=1"
    )
    _assert_filtered_results(response, expected_data, 6, 1, num_total)

    response = test_client.get(
        "/pacbio/wells?qc_status=aborted&page_size=2&page_number=2"
    )
    _assert_filtered_results(response, expected_data[2:4], 2, 2, num_total)

    response = test_client.get(
        "/pacbio/wells?qc_status=aborted&page_size=10&page_number=100"
    )
    _assert_filtered_results(response, [], 10, 100, num_total)


def _assert_filtered_results(
    response, expected_data, page_size, page_number, total_number
):
    """Convenience function to test the result of filtered well endpoint.

    Args:
        response: the response from the TestClient
        expected_data: dict mapping from run name to a dict mapping from well_label to QC state
    """

    assert response.status_code == 200

    resp = response.json()
    assert resp["page_size"] == page_size
    assert resp["page_number"] == page_number
    assert resp["total_number_of_items"] == total_number
    assert type(resp["wells"]) is list

    actual_data = []

    for result in resp["wells"]:
        rwell = result["run_name"] + ":" + result["label"]
        qc_state = (
            result["qc_state"]["qc_state"] if result["qc_state"] is not None else None
        )
        actual_data.append({rwell: qc_state})

    assert actual_data == expected_data
