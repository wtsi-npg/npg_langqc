import json

from fastapi.testclient import TestClient
from npg_id_generation.pac_bio import PacBioEntity

from lang_qc.models.qc_state import QcStateBasic
from tests.fixtures.inbox_data import test_data_factory


def test_change_non_existent_well(test_client: TestClient, test_data_factory):
    """Expect an error if we try to assign a state to a well which doesn't exist."""

    test_data = {
        "DONT-USE-THIS-RUN": {"A1": None, "B1": None},
        "NOR-THIS-ONE": {"A1": "Passed", "B1": "Failed"},
    }
    test_data_factory(test_data)

    post_data = """
        {
          "qc_type": "library",
          "qc_state": "Passed",
          "is_preliminary": true
        }
    """

    response = test_client.put(
        "/pacbio/run/NONEXISTENT/well/A0/qc_assign",
        post_data,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"] == "QC state of an unclaimed well cannot be updated"
    )


def test_change_outcome(test_client: TestClient, test_data_factory):
    """Successfully change a state from passed to failed"""

    test_data = {
        "MARATHON": {"A1": "Passed", "B1": None},
        "SEMI-MARATHON": {"D1": "Claimed"},
    }
    test_data_factory(test_data)

    post_data = """
        {
          "qc_type": "library",
          "qc_state": "Failed",
          "is_preliminary": false
        }
    """

    response = test_client.put(
        "/pacbio/run/MARATHON/well/A1/qc_assign",
        post_data,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    content = response.json()

    assert response.status_code == 200

    expected = {
        "id_product": PacBioEntity(
            run_name="MARATHON", well_label="A1"
        ).hash_product_id(),
        "user": "zx80@example.com",
        "qc_type": "library",
        "qc_state": "Failed",
        "is_preliminary": False,
        "created_by": "LangQC",
        "outcome": False,
    }

    for key, value in expected.items():
        assert content[key] == value
    for date_key in ("date_created", "date_updated"):
        assert content[date_key] is not None

    post_data = """
        {
          "qc_type": "library",
          "qc_state": "On hold",
          "is_preliminary": false
        }
    """
    response = test_client.put(
        "/pacbio/run/MARATHON/well/A1/qc_assign",
        post_data,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Error assigning status: QC state 'On hold' cannot be final"
    )

    post_data = """
        {
          "qc_type": "library",
          "qc_state": "On hold",
          "is_preliminary": true
        }
    """
    response = test_client.put(
        "/pacbio/run/MARATHON/well/A1/qc_assign",
        post_data,
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )
    content = response.json()

    expected["is_preliminary"] = True
    expected["outcome"] = None
    expected["qc_state"] = "On hold"

    assert response.status_code == 200
    for key, value in expected.items():
        assert content[key] == value


def test_error_on_invalid_state(test_client: TestClient, test_data_factory):
    """Test error when an invalid state is provided."""

    test_data = {
        "MARATHON": {"A1": "Passed", "B1": None},
        "SEMI-MARATHON": {"D1": "Claimed"},
    }
    test_data_factory(test_data)

    post_data = {
        "qc_type": "library",
        "qc_state": "NotDoingAnything",
        "is_preliminary": False,
    }

    response = test_client.put(
        "/pacbio/run/SEMI-MARATHON/well/D1/qc_assign",
        json.dumps(post_data),
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Error assigning status: QC state 'NotDoingAnything' is invalid"
    )


def test_error_on_unknown_user(test_client: TestClient, test_data_factory):
    """Test error when an unkown user makes a request."""

    test_data = {
        "MARATHON": {"A1": "Passed", "B1": None},
        "SEMI-MARATHON": {"D1": "Claimed"},
    }
    test_data_factory(test_data)

    post_data = {
        "qc_type": "library",
        "qc_state": "Failed",
        "is_preliminary": False,
    }

    response = test_client.put(
        "/pacbio/run/SEMI-MARATHON/well/D1/qc_assign",
        json.dumps(post_data),
        headers={"OIDC_CLAIM_EMAIL": "intruder@example.com"},
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "The user is not authorized to perform this operation."
    )


def test_error_on_unclaimed_well(test_client: TestClient, test_data_factory):
    """Test error on assigning a new state to an unclaimed well."""

    test_data = {"MARATHON": {"A1": None, "B1": None}}
    test_data_factory(test_data)

    post_data = {
        "qc_type": "library",
        "qc_state": "Passed",
        "is_preliminary": True,
    }

    response = test_client.put(
        "/pacbio/run/MARATHON/well/A1/qc_assign",
        json.dumps(post_data),
        headers={"OIDC_CLAIM_EMAIL": "zx80@example.com"},
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"] == "QC state of an unclaimed well cannot be updated"
    )


def test_error_on_preclaimed_well(test_client: TestClient, test_data_factory):
    """Test error on assigning a new state to a well claimed by another user."""

    test_data = {"MARATHON": {"A1": "Passed", "B1": None}}
    test_data_factory(test_data)

    post_data = {
        "qc_type": "library",
        "qc_state": "Passed",
        "is_preliminary": True,
    }

    response = test_client.put(
        "/pacbio/run/MARATHON/well/A1/qc_assign",
        json.dumps(post_data),
        headers={"OIDC_CLAIM_EMAIL": "cd32@example.com"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Unauthorised, QC is performed by another user"
