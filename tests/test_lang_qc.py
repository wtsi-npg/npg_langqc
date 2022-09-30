from fastapi.testclient import TestClient

from lang_qc import __version__


def test_version():
    assert __version__ == "0.2.0"


def test_not_found(test_client: TestClient):
    """Test a 404 response."""
    response = test_client.get("/this does not exist")
    assert response.status_code == 404
