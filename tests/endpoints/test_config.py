from fastapi.testclient import TestClient

from tests.fixtures.well_data import load_dicts_and_users


def test_get_config(test_client: TestClient, load_dicts_and_users):

    response = test_client.get("/config")
    assert response.status_code == 200
    expected = {
        "qc_flow_statuses": [
            {"label": "Inbox", "param": "inbox"},
            {"label": "In Progress", "param": "in_progress"},
            {"label": "On Hold", "param": "on_hold"},
            {"label": "QC Complete", "param": "qc_complete"},
            {"label": "Aborted", "param": "aborted"},
            {"label": "Unknown", "param": "unknown"},
            {"label": "Upcoming", "param": "upcoming"},
        ],
        "qc_states": [
            {"description": "Passed", "only_prelim": False},
            {"description": "Failed", "only_prelim": False},
            {"description": "Failed, Instrument", "only_prelim": False},
            {"description": "Failed, SMRT cell", "only_prelim": False},
            {"description": "On hold", "only_prelim": True},
            {"description": "On hold external", "only_prelim": True},
            {"description": "Undecided", "only_prelim": False},
        ],
    }
    assert response.json() == expected
