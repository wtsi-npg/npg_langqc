from fastapi.testclient import TestClient

from tests.conftest import insert_from_yaml
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_get_well_info(
    test_client: TestClient, mlwhdb_test_session, load_data4well_retrieval
):

    insert_from_yaml(
        mlwhdb_test_session, "tests/data/mlwh_pb_run_92", "lang_qc.db.mlwh_schema"
    )

    id_product = "cf18bd66e0f0895ea728c1d08103c62d3de8a57a5f879cee45f7b0acc028aa67"
    response = test_client.get(f"/pacbio/products/seq_level?id_product={id_product}")
    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == f"PacBio well for product ID {id_product} not found."
    )

    response = test_client.get("/pacbio/products/seq_level?id_product=342")
    assert response.status_code == 422
    assert response.json()["detail"].startswith("string does not match regex")

    id_product = "cf18bd66e0f0895ea728c1d08103c62d3de8a57a5f879cee45f7b0acc028aa61"
    response = test_client.get(f"/pacbio/products/seq_level?id_product={id_product}")
    assert response.status_code == 200
    result = response.json()

    assert result["label"] == "A1"
    assert result["run_name"] == "TRACTION-RUN-92"
    assert result["run_start_time"] == "2022-04-14T12:52:34"
    assert result["run_complete_time"] == "2022-04-20T09:16:53"
    assert result["well_start_time"] == "2022-04-14T13:02:48"
    assert result["well_complete_time"] == "2022-04-16T12:36:21"
    assert result["qc_state"] is None
    assert result["instrument_name"] == "64222E"
    assert result["instrument_type"] == "Sequel2e"
    assert result["plate_number"] is None
    assert result["id_product"] == id_product

    expected_metrics = {
        "smrt_link": {
            "run_uuid": "7f5d45ed-aa93-46a6-92b2-4b11d4bf29da",
            "dataset_uuid": "7f5d45ed-aa93-46a6-92b2-4b11d4bf29ro",
            "hostname": "pacbio01.dnapipelines.sanger.ac.uk",
        },
        "binding_kit": {"value": "Sequel II Binding Kit 2.2", "label": "Binding Kit"},
        "control_num_reads": {"value": 24837, "label": "Number of Control Reads"},
        "control_read_length_mean": {
            "value": 50169,
            "label": "Control Read Length (bp)",
        },
        "hifi_read_bases": {"value": 27.08, "label": "CCS Yield (Gb)"},
        "hifi_read_length_mean": {"value": 9411, "label": "CCS Mean Length (bp)"},
        "local_base_rate": {"value": 2.77, "label": "Local Base Rate"},
        "loading_conc": {"value": 80, "label": "Loading concentration (pM)"},
        "p0_num": {"value": 34.94, "label": "P0 %"},
        "p1_num": {"value": 62.81, "label": "P1 %"},
        "p2_num": {"value": 2.25, "label": "P2 %"},
        "polymerase_read_bases": {"value": 645.57, "label": "Total Cell Yield (Gb)"},
        "polymerase_read_length_mean": {
            "value": 128878,
            "label": "Mean Polymerase Read Length (bp)",
        },
        "movie_minutes": {"value": 30, "label": "Run Time (hr)"},
        "percentage_deplexed_reads": {
            "value": None,
            "label": "Percentage of reads deplexed",
        },
        "percentage_deplexed_bases": {
            "value": None,
            "label": "Percentage of bases deplexed",
        },
    }
    assert result["metrics"] == expected_metrics

    etrack = result["experiment_tracking"]
    assert etrack is not None
    assert etrack["num_samples"] == 1
    assert etrack["study_id"] == ["6457"]
    assert etrack["study_name"] == "Tree of Life - ASG"
    assert etrack["sample_id"] == "7880641"
    assert etrack["sample_name"] == "TOL_ASG12404704"
    assert etrack["library_type"] == ["PacBio_Ultra_Low_Input"]
    assert etrack["tag_sequence"] == []

    id_product = "c5babd5516f7b9faab8415927e5f300d5152bb96b8b922e768d876469a14fa5d"
    response = test_client.get(f"/pacbio/products/seq_level?id_product={id_product}")
    assert response.status_code == 200
    result = response.json()

    assert result["label"] == "D1"
    assert result["run_name"] == "TRACTION-RUN-92"
    assert result["instrument_name"] == "64222E"
    assert result["instrument_type"] == "Sequel2e"
    assert result["plate_number"] is None
    assert result["id_product"] == id_product
    assert result["metrics"]["smrt_link"]["dataset_uuid"] is None
    assert result["qc_state"] is None

    id_product = "b5a7d41453097fe3cc59644a679186e64a2147833ecc76a2870c5fe8068835ae"
    response = test_client.get(f"/pacbio/products/seq_level?id_product={id_product}")
    assert response.status_code == 200
    result = response.json()

    assert result["label"] == "B1"
    assert result["run_name"] == "TRACTION_RUN_1"
    assert result["instrument_name"] == "64016"
    assert result["instrument_type"] == "Sequel2"
    assert result["plate_number"] is None
    assert result["id_product"] == id_product
    assert result["experiment_tracking"] is None

    expected_qc_state = {
        "qc_state": "On hold",
        "is_preliminary": True,
        "qc_type": "sequencing",
        "outcome": None,
        "id_product": id_product,
        "date_created": "2022-12-08T07:15:19",
        "date_updated": "2022-12-08T07:15:19",
        "user": "zx80@example.com",
        "created_by": "LangQC",
    }
    assert result["qc_state"] == expected_qc_state

    id_product = "bc00984029864176324b91e0871a32a3692a54bd9b18f00b8596a2f2a166eca3"
    response = test_client.get(f"/pacbio/products/seq_level?id_product={id_product}")
    assert response.status_code == 200
    result = response.json()

    assert result["label"] == "A1"
    assert result["run_name"] == "TRACTION_RUN_2"
    assert result["instrument_name"] == "12345"
    assert result["instrument_type"] == "Revio"
    assert result["plate_number"] == 1
    assert result["id_product"] == id_product

    expected_qc_state = {
        "qc_state": "Failed, Instrument",
        "is_preliminary": True,
        "qc_type": "sequencing",
        "outcome": 0,
        "id_product": id_product,
        "date_created": "2022-12-07T15:13:56",
        "date_updated": "2022-12-07T15:13:56",
        "user": "zx80@example.com",
        "created_by": "LangQC",
    }
    assert result["qc_state"] == expected_qc_state

    # The same run and well as above, different plate.
    id_product = "3ff15eac7ac39e56d6ee2200b1b9a87a3da405911d79f5a1d250cca3ec697a9a"
    response = test_client.get(f"/pacbio/products/seq_level?id_product={id_product}")
    assert response.status_code == 200
    result = response.json()

    assert result["label"] == "A1"
    assert result["run_name"] == "TRACTION_RUN_2"
    assert result["instrument_name"] == "12345"
    assert result["instrument_type"] == "Revio"
    assert result["plate_number"] == 2
    assert result["id_product"] == id_product
    assert result["qc_state"] is None
