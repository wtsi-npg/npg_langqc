from fastapi.testclient import TestClient

from lang_qc import __version__
from tests.fixtures.inbox_data import inbox_data


def test_version():
    assert __version__ == "0.1.0"


def test_not_found(test_client: TestClient):
    """Test a 404 response."""
    response = test_client.get("/this does not exist")
    assert response.status_code == 404


def test_inbox(test_client: TestClient, inbox_data):
    """Test the inbox endpoint."""
    response = test_client.get("/pacbio/inbox?weeks=1")

    assert response.status_code == 200
    assert set([well["label"] for well in response.json()[0]["wells"]]) == set(
        [
            "A0",
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
        ]
    )

    response = test_client.get("/pacbio/inbox?weeks=2")
    assert response.status_code == 200
    assert set([well["label"] for well in response.json()[0]["wells"]]) == set(
        [
            "A0",
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
            "A7",
            "A8",
        ]
    )


def test_get_well(test_client: TestClient, inbox_data):
    """Test retrieving a well."""

    response = test_client.get("/pacbio/run/MARATHON/well/A0")
    assert response.status_code == 200
    result = response.json()

    assert result["run_info"]["well"]["label"] == "A0"
