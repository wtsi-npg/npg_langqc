# Copyright (c) 2022 Genome Research Ltd.
#
# Author: Adam Blanchet <ab59@sanger.ac.uk>
#
# This file is part of npg_langqc.
#
# npg_langqc is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from typing import List, Tuple

from fastapi.testclient import TestClient
from ml_warehouse.schema import PacBioRunWellMetrics
from sqlalchemy import select

from lang_qc.db.qc_schema import QcState, QcStateDict
from lang_qc.db.utils import get_well_metrics_from_qc_states
from lang_qc.endpoints.pacbio_well import (
    extract_well_label_and_run_name_from_state,
    pack_wells_and_states,
)
from tests.fixtures.inbox_data import inbox_data, test_data_factory, wells_and_states


def test_incorrect_filter(test_client: TestClient):
    """Expect a 422 response when an incorrect filter is given."""

    response = test_client.get(
        "/pacbio/wells?page_size=1&page_number=1&qc_status=thisdoesntexist"
    )
    assert response.status_code == 422

    response = test_client.get("/pacbio/wells?page_size=1&page_number=-1")
    assert response.status_code == 422  # positive value is expected
    response = test_client.get("/pacbio/wells?page_size=-11&page_number=1")
    assert response.status_code == 422  # positive value is expected

    response = test_client.get("/pacbio/wells")
    assert response.status_code == 422  # page size and number should be given

    response = test_client.get("/pacbio/wells?page_number=1")
    assert response.status_code == 422  # page size should be given

    response = test_client.get("/pacbio/wells?page_size=1")
    assert response.status_code == 422  # page number should be given


def assert_filtered_inbox_equals_expected(
    response, expected_data, page_size, page_number, total_number, qc_flow_status
):
    """Convenience function to test the result of filtered well endpoint.

    Args:
        response: the response from the TestClient
        expected_data: dict mapping from run name to a dict mapping from well_label to QC state
    """

    assert response.status_code == 200

    resp = response.json()
    assert resp["page_size"] == page_size
    assert resp["page_number"] == page_number
    assert resp["total_number_of_items"] == total_number
    assert resp["qc_flow_status"] == qc_flow_status
    assert type(resp["wells"]) is list

    actual_data = []

    for result in resp["wells"]:
        rwell = result["run_name"] + ":" + result["label"]
        qc_state = (
            result["qc_state"]["qc_state"] if result["qc_state"] is not None else None
        )
        actual_data.append({rwell: qc_state})
    assert actual_data == expected_data


def test_qc_complete_filter(test_client: TestClient, test_data_factory):
    """Test passing `qc_complete` filter."""

    desired_wells = {
        "MARATHON": {"A1": "Passed", "A2": "Passed", "A3": "On hold", "A4": None},
        "SEMI-MARATHON": {"A1": "Failed", "A2": "Claimed", "A3": "Claimed", "A4": None},
        "QUARTER-MILE": {"A1": None, "A2": "On hold", "A3": "On hold", "A4": None},
    }
    test_data_factory(desired_wells)
    status = "qc_complete"

    response = test_client.get(
        "/pacbio/wells?page_size=10&page_number=1&qc_status=" + status
    )

    expected_data = [
        {"MARATHON:A1": "Passed"},
        {"MARATHON:A2": "Passed"},
        {"SEMI-MARATHON:A1": "Failed"},
    ]
    assert_filtered_inbox_equals_expected(response, expected_data, 10, 1, 3, status)

    for well in response.json()["wells"]:
        assert well["run_start_time"] is not None
        assert well["run_complete_time"] is not None
        assert well["well_start_time"] is not None
        assert well["well_complete_time"] is not None

    response = test_client.get(
        "/pacbio/wells?page_size=10&page_number=2&qc_status=" + status
    )
    resp = response.json()
    assert resp["wells"] == []  # empty page
    assert resp["page_size"] == 10
    assert resp["page_number"] == 2
    assert resp["qc_flow_status"] == status
    assert resp["total_number_of_items"] == 3

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=1&qc_status=" + status
    )
    ed = expected_data[0:2]
    assert_filtered_inbox_equals_expected(response, ed, 2, 1, 3, status)

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=2&qc_status=" + status
    )
    ed = expected_data[2:]
    assert_filtered_inbox_equals_expected(response, ed, 2, 2, 3, status)


def test_on_hold_filter(test_client: TestClient, test_data_factory):
    """Test passing `on_hold` filter."""

    desired_wells = {
        "MARATHON": {"A1": "Passed", "A2": "Passed", "A3": "On hold", "A4": None},
        "SEMI-MARATHON": {"A1": "Failed", "A2": "Claimed", "A3": "Claimed", "A4": None},
        "QUARTER-MILE": {"A1": None, "A2": "On hold", "A3": "On hold", "A4": None},
    }
    test_data_factory(desired_wells)
    status = "on_hold"

    response = test_client.get(
        "/pacbio/wells?page_size=10&page_number=1&qc_status=" + status
    )
    expected_data = [
        {"MARATHON:A3": "On hold"},
        {"QUARTER-MILE:A2": "On hold"},
        {"QUARTER-MILE:A3": "On hold"},
    ]

    assert_filtered_inbox_equals_expected(response, expected_data, 10, 1, 3, status)

    response = test_client.get(
        "/pacbio/wells?page_size=10&page_number=2&qc_status=" + status
    )
    assert response.json()["wells"] == []  # empty page

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=1&qc_status=" + status
    )
    ed = expected_data[0:2]
    assert_filtered_inbox_equals_expected(response, ed, 2, 1, 3, status)

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=2&qc_status=" + status
    )
    ed = expected_data[2:]
    assert_filtered_inbox_equals_expected(response, ed, 2, 2, 3, status)


def test_in_progress_filter(test_client: TestClient, test_data_factory):
    """Test passing `in_progress` filter."""

    desired_wells = {
        "MARATHON": {"A1": "Passed", "A2": "Passed", "A3": "On hold", "A4": None},
        "SEMI-MARATHON": {"A1": "Failed", "A2": "Claimed", "A3": "Claimed", "A4": None},
        "QUARTER-MILE": {"A1": None, "A2": "On hold", "A3": "On hold", "A4": None},
    }
    test_data_factory(desired_wells)
    response = test_client.get(
        "/pacbio/wells?qc_status=in_progress&page_size=5&page_number=1"
    )
    expected_data = [
        {"SEMI-MARATHON:A2": "Claimed"},
        {"SEMI-MARATHON:A3": "Claimed"},
    ]

    assert_filtered_inbox_equals_expected(
        response, expected_data, 5, 1, 2, "in_progress"
    )


def test_inbox_filter(test_client: TestClient, test_data_factory):
    """Test passing `inbox` filter."""

    desired_wells = {
        "MARATHON": {"A1": "Passed", "A2": "Passed", "A3": "On hold", "A4": None},
        "SEMI-MARATHON": {"A1": "Failed", "A2": "Claimed", "A3": "Claimed", "A4": None},
        "QUARTER-MILE": {"A1": None, "A2": "On hold", "A3": "On hold", "A4": None},
    }
    test_data_factory(desired_wells)
    status = "inbox"

    expected_data = [
        {"MARATHON:A4": None},
        {"QUARTER-MILE:A1": None},
        {"QUARTER-MILE:A4": None},
        {"SEMI-MARATHON:A4": None},
    ]

    response = test_client.get("/pacbio/wells?page_size=100&page_number=1")
    assert_filtered_inbox_equals_expected(response, expected_data, 100, 1, 4, status)

    response = test_client.get(
        "/pacbio/wells?qc_status=inbox&page_size=100&page_number=1"
    )
    assert_filtered_inbox_equals_expected(response, expected_data, 100, 1, 4, status)

    response = test_client.get(
        "/pacbio/wells?page_size=100&page_number=2&qc_status=inbox"
    )
    assert response.json()["wells"] == []  # empty page

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=1&qc_status=inbox"
    )
    ed = expected_data[0:2]
    assert_filtered_inbox_equals_expected(response, ed, 2, 1, 4, status)

    response = test_client.get(
        "/pacbio/wells?page_size=2&page_number=2&qc_status=inbox"
    )
    ed = expected_data[2:]
    assert_filtered_inbox_equals_expected(response, ed, 2, 2, 4, status)


def test_with_more_data(test_client: TestClient, inbox_data):

    wells_list = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]
    response = test_client.get(
        "/pacbio/wells?qc_status=inbox&&page_size=20&page_number=1"
    )
    assert response.status_code == 200
    assert [well_item["label"] for well_item in response.json()["wells"]] == wells_list


def test_pack_well_and_states(wells_and_states):
    """Test lang_qc.endpoints.inbox.pack_well_and_states function."""

    wells, states = wells_and_states

    packed = pack_wells_and_states(wells, states)

    assert len(packed) == 7

    for well_entry in packed:
        assert well_entry.qc_state is not None


def test_extract_well_label_and_run_name_from_state(
    wells_and_states: Tuple[List[PacBioRunWellMetrics], List[QcState]]
):
    """Test lang_qc.endpoints.inbox.extract_well_label_and_run_name_from_state function."""
    wells, states = wells_and_states

    for well, state in zip(wells, states):
        assert (
            well.pac_bio_run_name,
            well.well_label,
        ) == extract_well_label_and_run_name_from_state(state)


def test_get_well_metrics_from_qc_states(
    qcdb_test_session, mlwhdb_test_session, test_data_factory
):
    """Test lang_qc.endpoints.get_well_metrics_from_qc_states function."""
    # Passing an empty list should return an empty list
    assert get_well_metrics_from_qc_states([], mlwhdb_test_session) == []

    desired_wells = {
        "MARATHON": {"A1": "Passed", "A2": "Passed", "A3": "On hold", "A4": None},
        "SEMI-MARATHON": {"A1": "Failed", "A2": "Claimed", "A3": "Claimed", "A4": None},
        "QUARTER-MILE": {"A1": None, "A2": "On hold", "A3": "On hold", "A4": None},
    }
    test_data_factory(desired_wells)
    states = (
        qcdb_test_session.execute(
            select(QcState).join(QcStateDict).where(QcStateDict.state == "On hold")
        )
        .scalars()
        .all()
    )

    corresponding_metrics = get_well_metrics_from_qc_states(states, mlwhdb_test_session)

    expected = set([("MARATHON", "A3"), ("QUARTER-MILE", "A2"), ("QUARTER-MILE", "A3")])
    actual = set(
        [(well.pac_bio_run_name, well.well_label) for well in corresponding_metrics]
    )

    assert expected == actual


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
    qc_data["p0_num"]["value"] = 32.47
    qc_data["p1_num"]["value"] = 65.98
    qc_data["p2_num"]["value"] = 1.55
    qc_data["polymerase_read_bases"]["value"] = 534.42
    qc_data["polymerase_read_length_mean"]["value"] = 101200
    qc_data["movie_minutes"]["value"] = 30

    assert result["run_info"]["well_label"] == "A1"
    assert result["run_info"]["library_type"] == "pipeline type 1"
    assert result["metrics"] == qc_data
