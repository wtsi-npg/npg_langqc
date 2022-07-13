import json

from tests.fixtures.inbox_data import test_data_factory

from fastapi.testclient import TestClient


def test_claim_nonexistent_well(test_client: TestClient, test_data_factory):
    """Expect an error if we try to claim a well which doesn't exist."""

    test_data = {
        "DONT-USE-THIS-RUN": {"A1": None, "B1": None},
        "NOR-THIS-ONE": {"A1": "Passed", "B1": "Failed"},
    }
    test_data_factory(test_data)

    post_data = {
        "user": "zx80",
        "qc_type": "library",
    }

    response = test_client.post(
        "/pacbio/run/NONEXISTENT/well/A0/qc_claim", json.dumps(post_data)
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Well A0 from run NONEXISTENT is not in the MLWH database."
    )


def test_claim_well_simple(test_client: TestClient, test_data_factory):
    """Successfully claim an unclaimed well."""

    test_data = {
        "MARATHON": {"A1": None, "B1": None},
        "SEMI-MARATHON": {"D1": "Claimed", "A1": "Passed"},
    }
    test_data_factory(test_data)

    post_data = {"user": "zx80", "qc_type": "library"}

    response = test_client.post(
        "/pacbio/run/MARATHON/well/B1/qc_claim", json.dumps(post_data)
    )

    assert response.status_code == 200

    actual_content = response.json()

    expected = {
        "user": "zx80",
        "qc_type": "library",
        "qc_type_description": "Sample/library evaluation",
        "qc_state": "Claimed",
        "is_preliminary": True,
        "created_by": "LangQC",
    }

    for key, expected_value in expected.items():
        assert actual_content[key] == expected_value


def test_claim_well_unknown_user(test_client: TestClient, test_data_factory):
    """Expect an error when claiming a well as an unknown user."""

    test_data = {
        "MARATHON": {"A1": None, "B1": None},
        "SEMI-MARATHON": {"D1": "Claimed", "A1": "Passed"},
    }
    test_data_factory(test_data)

    post_data = {"user": "Dave", "qc_type": "library"}

    response = test_client.post(
        "/pacbio/run/MARATHON/well/B1/qc_claim", json.dumps(post_data)
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "User has not been found in the QC database. Has it been registered?"
    )
