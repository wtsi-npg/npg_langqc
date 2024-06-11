from datetime import datetime

import pytest
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
    assert response.status_code == 200
    assert response.json() == {}

    response = test_client.post("/products/qc", json=[SHORT_CHECKSUM])
    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", 0]
    assert error["msg"] == "Value error, Invalid SHA256 checksum format"

    response = test_client.post("/products/qc", json=[BAD_STRING])
    assert response.status_code == 422

    response = test_client.post(
        "/products/qc", json=[FIRST_GOOD_CHECKSUM, SECOND_GOOD_CHECKSUM]
    )
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert FIRST_GOOD_CHECKSUM in response_data
    assert SECOND_GOOD_CHECKSUM in response_data
    list_1 = response_data[FIRST_GOOD_CHECKSUM]
    list_2 = response_data[SECOND_GOOD_CHECKSUM]
    qc_states = ["On hold external", "Failed, Instrument"]
    for index, l in enumerate([list_1, list_2]):
        assert len(l) == 2
        # The list of QC state objects contains QC states
        # for different QC types.
        assert {o["qc_type"] for o in l} == {"sequencing", "library"}
        assert {o["qc_state"] for o in l} == {qc_states[index]}

    response = test_client.post(
        "/products/qc", json=[MISSING_CHECKSUM, FIRST_GOOD_CHECKSUM]
    )
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert MISSING_CHECKSUM not in response_data
    assert FIRST_GOOD_CHECKSUM in response_data


def test_get_qc(test_client: TestClient, load_data4well_retrieval):

    response = test_client.get("/products/qc")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 0

    response = test_client.get("/products/qc?weeks=-1")
    assert response.status_code == 422

    # Earliest test QC states are updated on 2022-02-15
    interval = datetime.today() - datetime(year=2022, month=2, day=15)
    num_weeks = int(interval.days / 7 + 2)

    response = test_client.get(f"/products/qc?weeks={num_weeks}")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 18
    assert sum([len(l) for l in response_data.values()]) == 34

    response = test_client.get(
        f"/products/qc?weeks={num_weeks}&final=false&seq_level=no"
    )
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 18
    assert sum([len(l) for l in response_data.values()]) == 34

    response = test_client.get(f"/products/qc?weeks={num_weeks}&final=true")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 4
    assert sum([len(l) for l in response_data.values()]) == 8

    response = test_client.get(
        f"/products/qc?weeks={num_weeks}&final=True&seq_level=yes"
    )
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 4
    assert sum([len(l) for l in response_data.values()]) == 4
    product_id = "5e91b9246b30c2df4e9f2a2313ce097e93493b0a822e9d9338e32df5d58db585"
    assert product_id in response_data
    qc_state = response_data[product_id][0]
    assert qc_state["id_product"] == product_id
    assert qc_state["is_preliminary"] is False
    assert qc_state["qc_type"] == "sequencing"
