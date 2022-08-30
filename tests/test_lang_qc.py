from fastapi.testclient import TestClient

from lang_qc import __version__
from tests.fixtures.inbox_data import inbox_data


def test_version():
    assert __version__ == "0.2.0"


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
    """Test retrieving a well with and without QC data."""

    response = test_client.get("/pacbio/run/MARATHON/well/A0")
    assert response.status_code == 200
    result = response.json()

    assert result["run_info"]["well_label"] == "A0"
    assert result["run_info"]["library_type"] == "pipeline type 1"
    qc_data = {
        "smrt_link": {"run_uuid": None, "hostname": None},
        "binding_kit": {"value": None, "label": "Binding Kit"},
        "control_num_reads": {"value": None, "label": "Number of Control Reads"},
        "control_read_length_mean": {
            "value": None,
            "label": "Control Read Length (bp)",
        },
        "hifi_read_bases": {"value": None, "label": "CCS Yield (Gb)"},
        "hifi_read_length_mean": {"value": None, "label": "CCS Mean Length (bp)"},
        "local_base_rate": {"value": None, "label": "Local Base Rate"},
        "p0_num": {"value": None, "label": "P0 %"},
        "p1_num": {"value": None, "label": "P1 %"},
        "p2_num": {"value": None, "label": "P2 %"},
        "polymerase_read_bases": {"value": None, "label": "Total Cell Yield (Gb)"},
        "polymerase_read_length_mean": {
            "value": None,
            "label": "Mean Polymerase Read Length (bp)",
        },
        "movie_minutes": {"value": None, "label": "Run Time (hr)"},
    }
    assert result["metrics"] == qc_data

    response = test_client.get("/pacbio/run/MARATHON/well/A1")
    assert response.status_code == 200
    result = response.json()

    qc_data["smrt_link"] = {
        "run_uuid": "05b0a368-2548-11ed-861d-0242ac120002",
        "hostname": "esa_host",
    }
    qc_data["binding_kit"]["value"] = "Sequel II Binding Kit 2.2"
    qc_data["control_num_reads"]["value"] = 7400
    qc_data["control_read_length_mean"]["value"] = 51266
    qc_data["hifi_read_bases"]["value"] = 28.53
    qc_data["hifi_read_length_mean"]["value"] = 11619
    qc_data["local_base_rate"]["value"] = 2.73
    qc_data["p0_num"]["value"] = 32.50
    qc_data["p1_num"]["value"] = 66.04
    qc_data["p2_num"]["value"] = 1.55
    qc_data["polymerase_read_bases"]["value"] = 534.42
    qc_data["polymerase_read_length_mean"]["value"] = 101200
    qc_data["movie_minutes"]["value"] = 30

    assert result["run_info"]["well_label"] == "A1"
    assert result["run_info"]["library_type"] == "pipeline type 1"
    assert result["metrics"] == qc_data
