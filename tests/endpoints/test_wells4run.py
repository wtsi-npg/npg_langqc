from fastapi.testclient import TestClient

from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_nonexisting_run(test_client: TestClient):

    response = test_client.get("/pacbio/run/xxxx")
    assert response.status_code == 404
    assert response.json() == {"detail": "Metrics data for run 'xxxx' is not found"}


def test_existing_run(test_client: TestClient, load_data4well_retrieval):

    # Rely on default paging
    response = test_client.get("/pacbio/run/TRACTION_RUN_1")
    assert response.status_code == 200
    resp = response.json()
    assert resp["page_size"] == 20
    assert resp["page_number"] == 1
    assert resp["total_number_of_items"] == 4
    assert type(resp["wells"]) is list
    assert len(resp["wells"]) == 4
    run_names = [well["run_name"] for well in resp["wells"]]
    assert run_names == 4 * ["TRACTION_RUN_1"]
    label_list = [well["label"] for well in resp["wells"]]
    assert label_list == ["A1", "B1", "C1", "D1"]
    qc_states = [well["qc_state"]["qc_state"] for well in resp["wells"]]
    assert qc_states == ["Claimed", "On hold", "Claimed", "On hold external"]

    assert (
        resp["wells"][0]["instrument_name"] == "64016"
    ), "Instrument name was propagated"
    assert (
        resp["wells"][0]["instrument_type"] == "Sequel2"
    ), "Instrument type was propagated"

    # Use custom paging.
    response = test_client.get("/pacbio/run/TRACTION_RUN_1?page_size=2&page_number=2")
    assert response.status_code == 200
    resp = response.json()
    assert resp["page_size"] == 2
    assert resp["page_number"] == 2
    assert resp["total_number_of_items"] == 4
    assert len(resp["wells"]) == 2
