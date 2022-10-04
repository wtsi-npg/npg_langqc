from fastapi.testclient import TestClient

from lang_qc import __version__


def test_version():
    assert __version__ == "0.2.0"


def test_not_found(test_client: TestClient):
    """Test a 404 response."""
    response = test_client.get("/this does not exist")
    assert response.status_code == 404


def test_get_qc_flow_states(test_client: TestClient):
    response = test_client.get("/config")
    assert response.status_code == 200
    expected = {
        "qc_flow_statuses": [
            {"label": "Inbox", "param": "inbox"},
            {"label": "In Progress", "param": "in_progress"},
            {"label": "On Hold", "param": "on_hold"},
            {"label": "QC Complete", "param": "qc_complete"},
        ]
    }
    assert response.json() == expected
