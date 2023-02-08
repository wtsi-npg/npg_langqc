from fastapi.testclient import TestClient

from tests.fixtures.inbox_data import test_data_factory


def test_get_qc_by_product_id(test_client: TestClient, test_data_factory):

    test_data_factory({"TEST-1": {"A1": "Passed"}, "TEST-2": {"A1": "Failed"}})

    FIRST_GOOD_CHECKSUM = (
        "79f8e7f50a28c0c5bd17bfc52e4985cc37f83ffb40424444f45d38a7b3a8dc7b"
    )
    SECOND_GOOD_CHECKSUM = (
        "2ad6579de8a943a1c11fce8a6ea42af97f5bd285424cb5415840f2b663d8488e"
    )
    MISSING_CHECKSUM = "A" * 64
    SHORT_CHECKSUM = "AAAAAAAAAAAAAAAAAAA"
    BAD_STRING = "exec('rm -rf /')"

    response = test_client.post("/products/qc", json=[MISSING_CHECKSUM])
    assert response.ok is True
    assert response.json() == {}

    response = test_client.post("/products/qc", json=[SHORT_CHECKSUM])
    assert response.ok is False
    assert response.status_code == 422
    message = response.json()["detail"]
    assert message == "Checksum must be hexadecimal of length 64"

    response = test_client.post("/products/qc", json=[BAD_STRING])
    assert response.ok is False
    assert response.status_code == 422

    response = test_client.post(
        "/products/qc", json=[FIRST_GOOD_CHECKSUM, SECOND_GOOD_CHECKSUM]
    )
    assert response.ok is True
    response_data = response.json()
    assert FIRST_GOOD_CHECKSUM in response_data
    assert SECOND_GOOD_CHECKSUM in response_data

    assert response_data[FIRST_GOOD_CHECKSUM]["sequencing"]["qc_state"] == "Passed"
    assert response_data[SECOND_GOOD_CHECKSUM]["sequencing"]["qc_state"] == "Failed"

    response = test_client.post(
        "/products/qc", json=[MISSING_CHECKSUM, FIRST_GOOD_CHECKSUM]
    )
    assert response.ok is True
    response_data = response.json()
    assert MISSING_CHECKSUM not in response_data
    assert FIRST_GOOD_CHECKSUM in response_data

    assert response_data[FIRST_GOOD_CHECKSUM]["sequencing"]["qc_state"] == "Passed"
