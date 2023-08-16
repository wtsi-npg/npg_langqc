from fastapi.testclient import TestClient
from npg_id_generation.pac_bio import PacBioEntity

from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users

id_product_2A1 = PacBioEntity(
    run_name="TRACTION_RUN_2", well_label="A1", plate_number=1
).hash_product_id()
post_data = """
{
    "qc_type": "sequencing",
    "qc_state": "Passed",
    "is_preliminary": true
}
"""


def test_error_invalid_product_id(test_client: TestClient, load_data4well_retrieval):
    """Error if product ID validation fails."""

    response = test_client.put(
        "/pacbio/products/12345q/qc_assign",
        post_data,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == [
        {
            "loc": ["path", "id_product"],
            "msg": "Invalid SHA256 checksum format",
            "type": "value_error",
        }
    ]


def test_error_nonexistent_well(test_client: TestClient, load_data4well_retrieval):
    """Expect an error if we try to update a well which doesn't exist."""

    id = 32 * "a" + 32 * "b"
    response = test_client.put(
        f"/pacbio/products/{id}/qc_assign",
        post_data,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == f"PacBio well for product ID {id} not found."


def test_error_unknown_user(test_client: TestClient, load_data4well_retrieval):
    """Expect an error when updating a well as an unknown user."""

    response = test_client.put(
        f"/pacbio/products/{id_product_2A1}/qc_assign",
        post_data,
        headers={"OIDC_CLAIM_EMAIL": "intruder@example.com"},
    )
    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "The user is not authorized to perform this operation."
    )


def test_error_no_user(test_client: TestClient, load_data4well_retrieval):
    """Expect an error when updating a well if no user is in the header."""

    response = test_client.put(
        f"/pacbio/products/{id_product_2A1}/qc_assign", post_data
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "No user provided, is the user logged in?"


def test_error_updating_unclaimed_well(
    test_client: TestClient, load_data4well_retrieval
):
    """Expect an error when updating an unclaimed well."""

    id_product_15A1 = PacBioEntity(
        run_name="TRACTION_RUN_15", well_label="A1", plate_number=1
    ).hash_product_id()
    response = test_client.put(
        f"/pacbio/products/{id_product_15A1}/qc_assign",
        post_data,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 409
    assert (
        response.json()["detail"] == "QC state of an unclaimed well cannot be updated"
    )


def test_error_inconsistent_preliminary_flag(
    test_client: TestClient, load_data4well_retrieval
):

    post_data_prelim = """
    {
        "qc_type": "sequencing",
        "qc_state": "On hold",
        "is_preliminary": false
    }
    """
    response = test_client.put(
        f"/pacbio/products/{id_product_2A1}/qc_assign",
        post_data_prelim,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Error assigning status: QC state 'On hold' cannot be final"
    )


def test_error_invalid_state(test_client: TestClient, load_data4well_retrieval):
    """Test error when an invalid state is provided."""

    post_data_state = """
    {
        "qc_type": "sequencing",
        "qc_state": "On reprimand",
        "is_preliminary": false
    }
    """
    response = test_client.put(
        f"/pacbio/products/{id_product_2A1}/qc_assign",
        post_data_state,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Error assigning status: QC state 'On reprimand' is invalid"
    )


def test_assign_state(test_client: TestClient, load_data4well_retrieval):
    """Successfully change a state from passed to failed"""

    response = test_client.put(
        f"/pacbio/products/{id_product_2A1}/qc_assign",
        post_data,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    content = response.json()

    assert response.status_code == 200

    expected = {
        "id_product": id_product_2A1,
        "user": "zx80@example.com",
        "qc_type": "sequencing",
        "qc_state": "Passed",
        "is_preliminary": True,
        "created_by": "LangQC",
        "outcome": True,
    }

    for key, value in expected.items():
        assert content[key] == value
    for date_key in ("date_created", "date_updated"):
        assert content[date_key] is not None

    post_data_update = """
    {
        "qc_type": "sequencing",
        "qc_state": "On hold",
        "is_preliminary": true
    }
    """
    response = test_client.put(
        f"/pacbio/products/{id_product_2A1}/qc_assign",
        post_data_update,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    content = response.json()

    expected["is_preliminary"] = True
    expected["outcome"] = None
    expected["qc_state"] = "On hold"

    assert response.status_code == 200
    for key, value in expected.items():
        assert content[key] == value


def test_permutations_of_plates(test_client: TestClient, load_data4well_retrieval):

    post_data_update = """
    {
        "qc_type": "sequencing",
        "qc_state": "Passed",
        "is_preliminary": true
    }
    """

    # Sequel2 instrument - plate number is undefined (not relevant).
    id_product_1A1 = PacBioEntity(
        run_name="TRACTION_RUN_1", well_label="A1"
    ).hash_product_id()
    response = test_client.put(
        f"/pacbio/products/{id_product_1A1}/qc_assign",
        post_data_update,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 200

    # Revio instrument plates No 1&2.
    for pn in [1, 2]:
        id_product = PacBioEntity(
            run_name="TRACTION_RUN_16", well_label="A1", plate_number=pn
        ).hash_product_id()
        response = test_client.put(
            f"/pacbio/products/{id_product}/qc_assign",
            post_data_update,
            headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
        )
        assert response.status_code == 200
        r = response.json()
        assert r["qc_state"] == "Passed"
        assert r["id_product"] == id_product
