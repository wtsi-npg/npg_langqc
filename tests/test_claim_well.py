import json

from fastapi.testclient import TestClient
from npg_id_generation.pac_bio import PacBioEntity

from tests.fixtures.inbox_data import test_data_factory


def test_claim_nonexistent_well(test_client: TestClient, test_data_factory):
    """Expect an error if we try to claim a well which doesn't exist."""

    test_data = {
        "DONT-USE-THIS-RUN": {"A1": None, "B1": None},
        "NOR-THIS-ONE": {"A1": "Passed", "B1": "Failed"},
    }
    test_data_factory(test_data)

    response = test_client.post(
        "/pacbio/run/NONEXISTENT/well/A0/qc_claim",
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Well A0 run NONEXISTENT does not exist"


def test_claim_well_simple(test_client: TestClient, test_data_factory):
    """Successfully claim an unclaimed well."""

    test_data = {
        "MARATHON": {"A1": None, "B1": None},
        "SEMI-MARATHON": {"D1": "Claimed", "A1": "Passed"},
    }
    test_data_factory(test_data)

    response = test_client.post(
        "/pacbio/run/MARATHON/well/B1/qc_claim",
        headers={"oidc_claim_email": "zx80@example.com"},
    )

    assert response.status_code == 201

    actual_content = response.json()

    expected = {
        "id_product": PacBioEntity(
            run_name="MARATHON", well_label="B1"
        ).hash_product_id(),
        "user": "zx80@example.com",
        "qc_type": "sequencing",
        "qc_state": "Claimed",
        "is_preliminary": True,
        "created_by": "LangQC",
        "outcome": None,
    }

    for key, expected_value in expected.items():
        assert actual_content[key] == expected_value
    for date_key in ("date_created", "date_updated"):
        assert actual_content[date_key] is not None


def test_claim_well_unknown_user(test_client: TestClient, test_data_factory):
    """Expect an error when claiming a well as an unknown user."""

    test_data = {
        "MARATHON": {"A1": None, "B1": None},
        "SEMI-MARATHON": {"D1": "Claimed", "A1": "Passed"},
    }
    test_data_factory(test_data)

    response = test_client.post(
        "/pacbio/run/MARATHON/well/B1/qc_claim",
        headers={"OIDC_CLAIM_EMAIL": "intruder@example.com"},
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "The user is not authorized to perform this operation."
    )


def test_error_on_no_user(test_client: TestClient, test_data_factory):
    """Expect an error when claiming a well if no user is in the header."""

    test_data = {"MARATHON": {"A1": "Failed", "B1": None}}

    test_data_factory(test_data)

    for well_label in "A1", "B1":

        response = test_client.post(f"/pacbio/run/MARATHON/well/{well_label}/qc_claim")

        assert response.status_code == 401
        assert response.json()["detail"] == "No user provided, is the user logged in?"


def test_error_on_already_claimed(test_client: TestClient, test_data_factory):
    """Expect an error when claiming a well which has already been claimed"""

    test_data = {
        "MARATHON": {"A1": "Failed", "B1": "On hold"},
        "SEMI-MARATHON": {"D1": "Claimed", "A1": "Passed"},
    }
    test_data_factory(test_data)

    for run_name in test_data:
        for well_label in test_data[run_name]:

            response = test_client.post(
                f"/pacbio/run/{run_name}/well/{well_label}/qc_claim",
                headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
            )
            assert response.status_code == 409
            assert (
                response.json()["detail"]
                == f"Well {well_label} run {run_name} has already been claimed"
            )
