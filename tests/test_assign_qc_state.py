import json

from tests.fixtures.inbox_data import test_data_factory

from fastapi.testclient import TestClient
import pytest

from lang_qc.models.inbox_models import QcStatus
from lang_qc.models.qc_state_models import QcStatusAssignmentPostBody


def test_change_non_existent_well(test_client: TestClient, test_data_factory):
    """Expect an error if we try to assign a state to a well which doesn't exist."""

    test_data = {
        "DONT-USE-THIS-RUN": {"A1": None, "B1": None},
        "NOR-THIS-ONE": {"A1": "Passed", "B1": "Failed"},
    }
    test_data_factory(test_data)

    post_data = """
        {
          "user": "zx80",
          "qc_type": "library",
          "qc_state": "Passed",
          "is_preliminary": true
        }
    """

    response = test_client.post("/pacbio/run/NONEXISTENT/well/A0/qc_assign", post_data)

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Well A0 from run NONEXISTENT is not in the MLWH database."
    )


def test_change_from_passed_to_fail(test_client: TestClient, test_data_factory):
    """Successfully change a state from passed to failed"""

    test_data = {
        "MARATHON": {"A1": "Passed", "B1": None},
        "SEMI-MARATHON": {"D1": "Claimed"},
    }
    test_data_factory(test_data)

    post_data = """
        {
          "user": "zx80",
          "qc_type": "library",
          "qc_state": "Failed",
          "is_preliminary": false
        }
    """

    response = test_client.post("/pacbio/run/MARATHON/well/A1/qc_assign", post_data)

    assert response.status_code == 200

    content = response.json()

    expected = {
        "user": "zx80",
        "qc_type": "library",
        "qc_type_description": "Sample/library evaluation",
        "qc_state": "Failed",
        "is_preliminary": False,
        "created_by": "LangQC",
    }

    for key, value in expected.items():
        assert content[key] == value


@pytest.mark.parametrize(
    "invalid_argument,expected_message",
    [
        ("qc_type", "QC type is not in the QC database."),
        (
            "user",
            "User has not been found in the QC database. Have they been registered?",
        ),
        (
            "qc_state",
            "Desired QC state is not in the QC database. It might not be allowed.",
        ),
    ],
)
def test_error_on_invalid_values(
    test_client: TestClient, test_data_factory, invalid_argument, expected_message
):
    """Test errors returned when invalid arguments are provided."""

    test_data = {
        "MARATHON": {"A1": "Passed", "B1": None},
        "SEMI-MARATHON": {"D1": "Claimed"},
    }
    test_data_factory(test_data)

    post_data = {
        "user": "zx80",
        "qc_type": "library",
        "qc_state": "Failed",
        "is_preliminary": False,
    }

    post_data[invalid_argument] = "invalidvalue"
    response = test_client.post(
        f"/pacbio/run/SEMI-MARATHON/well/D1/qc_assign", json.dumps(post_data)
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"] == f"An error occured: {expected_message}\n"
        f"Request body was: {QcStatusAssignmentPostBody.parse_obj(post_data).json()}"
    )


def test_error_on_unclaimed_well(test_client: TestClient, test_data_factory):
    """Test error on assigning a new state to an unclaimed well."""

    test_data = {"MARATHON": {"A1": None, "B1": None}}
    test_data_factory(test_data)

    post_data = {
        "user": "zx80",
        "qc_type": "library",
        "qc_state": "Passed",
        "is_preliminary": True,
    }

    response = test_client.post(
        "/pacbio/run/MARATHON/well/A1/qc_assign", json.dumps(post_data)
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Cannot assign a state to a well which has not yet been claimed."
    )


def test_error_on_preclaimed_well(test_client: TestClient, test_data_factory):
    """Test error on assigning a new state to a well claimed by another user."""

    test_data = {"MARATHON": {"A1": "Passed", "B1": None}}
    test_data_factory(test_data)

    post_data = {
        "user": "cd32",
        "qc_type": "library",
        "qc_state": "Passed",
        "is_preliminary": True,
    }

    response = test_client.post(
        "/pacbio/run/MARATHON/well/A1/qc_assign", json.dumps(post_data)
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Cannot assign a state to a well which has been claimed by another user."
    )
