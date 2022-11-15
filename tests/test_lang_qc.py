from fastapi.testclient import TestClient

from lang_qc import __version__
from tests.fixtures.inbox_data import test_data_factory


def test_version():
    assert __version__ == "0.2.0"


def test_not_found(test_client: TestClient):
    """Test a 404 response."""
    response = test_client.get("/this does not exist")
    assert response.status_code == 404


def test_get_config(test_client: TestClient, test_data_factory):
    test_data_factory({})
    response = test_client.get("/config")
    assert response.status_code == 200
    expected = {
        "qc_flow_statuses": [
            {"label": "Inbox", "param": "inbox"},
            {"label": "In Progress", "param": "in_progress"},
            {"label": "On Hold", "param": "on_hold"},
            {"label": "QC Complete", "param": "qc_complete"},
        ],
        "qc_states": [
            {"description": "Passed", "only_prelim": False},
            {"description": "Failed", "only_prelim": False},
            {"description": "On hold", "only_prelim": True},
        ],
    }
    assert response.json() == expected
