from fastapi.testclient import TestClient

from tests.fixtures.inbox_data import test_data_factory


def test_get_qc_by_product_id(test_client: TestClient, test_data_factory):

    test_data_factory({"TEST-1": {"A1": "Passed"}, "TEST-2": {"A1": "Failed"}})

    response = test_client.post("/pacbio/wells/qc", json=["AAAAAAAAAAAAAAAAAAA"])
    assert response.ok is True
    assert response.json() == {}

    checksums = [
        "79f8e7f50a28c0c5bd17bfc52e4985cc37f83ffb40424444f45d38a7b3a8dc7b",
        "2ad6579de8a943a1c11fce8a6ea42af97f5bd285424cb5415840f2b663d8488e",
    ]

    response = test_client.post("/pacbio/wells/qc", json=checksums)

    response_data = response.json()
    for cs in checksums:
        assert cs in response_data

    assert response_data[checksums[0]]["sequencing"]["qc_state"] == "Passed"
    assert response_data[checksums[1]]["sequencing"]["qc_state"] == "Failed"
