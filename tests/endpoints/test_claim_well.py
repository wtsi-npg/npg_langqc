from datetime import datetime

from fastapi.testclient import TestClient
from npg_id_generation.pac_bio import PacBioEntity

from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users

# Revio instrument - plate No 1
id_product_15A1 = PacBioEntity(
    run_name="TRACTION_RUN_15", well_label="A1", plate_number=1
).hash_product_id()


def test_id_generation_rule():
    """
    Demo that plate No 1 is equivalent to plate number being
    undefined. This is to ensure backwards compatibility with
    Revio wells, which were QC-ed prior to the introduction
    of plate numbers.
    """

    assert (
        id_product_15A1
        == PacBioEntity(run_name="TRACTION_RUN_15", well_label="A1").hash_product_id()
    )


def test_claim_invalid_product_id(test_client: TestClient, load_data4well_retrieval):
    """Error if product ID validation fails."""

    response = test_client.post(
        "/pacbio/products/12345q/qc_claim",
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 422
    assert response.json()["detail"].startswith("string does not match regex")


def test_claim_nonexistent_well(test_client: TestClient, load_data4well_retrieval):
    """Expect an error if we try to claim a well which doesn't exist."""

    id = 32 * "a" + 32 * "b"
    response = test_client.post(
        f"/pacbio/products/{id}/qc_claim",
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == f"PacBio well for product ID {id} not found."


def test_claim_well_unknown_user(test_client: TestClient, load_data4well_retrieval):
    """Expect an error when claiming a well as an unknown user."""

    response = test_client.post(
        f"/pacbio/products/{id_product_15A1}/qc_claim",
        headers={"OIDC_CLAIM_EMAIL": "intruder@example.com"},
    )
    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "The user is not authorized to perform this operation."
    )


def test_error_on_no_user(test_client: TestClient, load_data4well_retrieval):
    """Expect an error when claiming a well if no user is in the header."""

    response = test_client.post(f"/pacbio/products/{id_product_15A1}/qc_claim")
    assert response.status_code == 401
    assert response.json()["detail"] == "No user provided, is the user logged in?"


def test_claim_well_successful(test_client: TestClient, load_data4well_retrieval):
    """Successfully claim an unclaimed well."""

    time_now = datetime.now()

    response = test_client.post(
        f"/pacbio/products/{id_product_15A1}/qc_claim",
        headers={"oidc_claim_email": "zx80@example.com"},
    )
    assert response.status_code == 201

    actual_content = response.json()

    expected = {
        "id_product": id_product_15A1,
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
        delta = (
            datetime.strptime(actual_content[date_key], "%Y-%m-%dT%H:%M:%S") - time_now
        )
        assert delta.total_seconds() <= 1


def test_error_on_already_claimed(test_client: TestClient, load_data4well_retrieval):
    """Expect an error when claiming a well which has already been claimed"""

    response = test_client.post(
        f"/pacbio/products/{id_product_15A1}/qc_claim",
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == f"Well for product {id_product_15A1} has already been claimed"
    )


def test_permutations_of_plates(test_client: TestClient, load_data4well_retrieval):

    # Sequel2 instrument - plate number is undefined (not relevant).
    id_product_14A1 = PacBioEntity(
        run_name="TRACTION_RUN_14", well_label="A1"
    ).hash_product_id()

    response = test_client.post(
        f"/pacbio/products/{id_product_14A1}/qc_claim",
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 201

    # Revio instrument plate No 2.
    # The same well on plate 1 has QC state assigned in fixtures.
    id_product_2A1_2 = PacBioEntity(
        run_name="TRACTION_RUN_2", well_label="A1", plate_number=2
    ).hash_product_id()
    response = test_client.post(
        f"/pacbio/products/{id_product_2A1_2}/qc_claim",
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 201
