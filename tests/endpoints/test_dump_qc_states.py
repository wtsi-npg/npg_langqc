from fastapi.testclient import TestClient

from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_get_qc_by_product_id(test_client: TestClient, load_data4well_retrieval):

    # "TRACTION_RUN_1", "D1", "On hold", Final
    FIRST_GOOD_CHECKSUM = (
        "6657a34aa6159d7e2426f4732a84c51fa2d9186a4578e61ec21de4cb028fc800"
    )
    # "TRACTION_RUN_2", "B1", "Failed, Instrument", Preliminary
    SECOND_GOOD_CHECKSUM = (
        "e47765a207c810c2c281d5847e18c3015f3753b18bd92e8a2bea1219ba3127ea"
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
    assert len(response_data) == 2
    assert FIRST_GOOD_CHECKSUM in response_data
    assert SECOND_GOOD_CHECKSUM in response_data
    list_1 = response_data[FIRST_GOOD_CHECKSUM]
    list_2 = response_data[SECOND_GOOD_CHECKSUM]
    qc_states = ["On hold", "Failed, Instrument"]
    for index, l in enumerate([list_1, list_2]):
        assert len(l) == 2
        # The list of QC state objects contains QC states
        # for different QC types.
        assert {o["qc_type"] for o in l} == {"sequencing", "library"}
        assert {o["qc_state"] for o in l} == {qc_states[index]}

    response = test_client.post(
        "/products/qc", json=[MISSING_CHECKSUM, FIRST_GOOD_CHECKSUM]
    )
    assert response.ok is True
    response_data = response.json()
    assert len(response_data) == 1
    assert MISSING_CHECKSUM not in response_data
    assert FIRST_GOOD_CHECKSUM in response_data
