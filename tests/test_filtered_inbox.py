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
from sqlalchemy.orm import Session

from lang_qc.db.qc_schema import (
    QcState,
    QcStateDict,
    SubProduct,
    ProductLayout,
    SeqProduct,
)
from lang_qc.endpoints.inbox import (
    pack_wells_and_states,
    extract_well_label_and_run_name_from_state,
    get_well_metrics_from_qc_states,
)
from lang_qc.models.inbox_models import FilteredInboxResults

from tests.fixtures.inbox_data import (
    filtered_inbox_data,
    inbox_data,
    wells_and_states,
)


def test_incorrect_filter(test_client: TestClient):
    """Expect a 422 response when an incorrect filter is given."""

    response = test_client.get("/pacbio/wells?qc_status=thisdoesntexist")
    assert response.status_code == 422


def assert_filtered_inbox_equals_expected(response, expected_data):
    """Convenience function to test the result of filtered well endpoint.

    Args:
        response: the response from the TestClient
        expected_data: dict mapping from run name to a dict mapping from well_label to QC state
    """

    assert response.status_code == 200
    content = FilteredInboxResults.parse_obj(response.json())

    # We try to unpack the data to make expected data again

    actual_data = {}

    for result in content.__root__:
        wells = {}
        for well_info in result.wells:
            wells[well_info.label] = (
                well_info.qc_status.qc_state
                if well_info.qc_status is not None
                else None
            )
        actual_data[result.run_name] = wells

    assert actual_data == expected_data


def test_qc_complete_filter(test_client: TestClient, filtered_inbox_data):
    """Test passing `qc_complete` filter."""

    response = test_client.get("/pacbio/wells?qc_status=qc_complete")

    expected_data = {
        "MARATHON": {"A1": "Passed", "A2": "Passed"},
        "SEMI-MARATHON": {"A1": "Failed"},
    }
    assert_filtered_inbox_equals_expected(response, expected_data)


def test_on_hold_filter(test_client: TestClient, filtered_inbox_data):
    """Test passing `on_hold` filter."""

    response = test_client.get("/pacbio/wells?qc_status=on_hold")
    expected_data = {
        "MARATHON": {"A3": "On hold"},
        "QUARTER-MILE": {"A2": "On hold", "A3": "On hold"},
    }

    assert_filtered_inbox_equals_expected(response, expected_data)


def test_in_progress_filter(test_client: TestClient, filtered_inbox_data):
    """Test passing `in_progress` filter."""

    response = test_client.get("/pacbio/wells?qc_status=in_progress")
    expected_data = {
        "SEMI-MARATHON": {"A3": "Claimed", "A2": "Claimed"},
    }

    assert_filtered_inbox_equals_expected(response, expected_data)


def test_inbox_filter(test_client: TestClient, filtered_inbox_data):
    """Test passing `inbox` filter."""

    response = test_client.get("/pacbio/wells?qc_status=inbox")
    expected_data = {
        "MARATHON": {"A4": None},
        "SEMI-MARATHON": {"A4": None},
        "QUARTER-MILE": {"A1": None, "A4": None},
    }

    assert_filtered_inbox_equals_expected(response, expected_data)


def test_default_filter(test_client: TestClient, filtered_inbox_data):
    """Test passing no filter, equivalent to `inbox` filter."""

    response = test_client.get("/pacbio/wells?qc_status=inbox")
    expected_data = {
        "MARATHON": {"A4": None},
        "SEMI-MARATHON": {"A4": None},
        "QUARTER-MILE": {"A1": None, "A4": None},
    }

    assert_filtered_inbox_equals_expected(response, expected_data)


def test_pack_well_and_states(wells_and_states):
    """Test lang_qc.endpoints.inbox.pack_well_and_states function."""

    wells, states = wells_and_states

    packed: FilteredInboxResults = pack_wells_and_states(wells, states)

    # Count the wells in packed
    count = 0
    for entry in packed:
        count += len(entry.wells)

    assert len(wells) == count

    for entry in packed:
        # Check that each result has a corresponding qc_status and
        # that all wells are accounted for.
        for well in entry.wells:
            assert well.qc_status is not None

        corresponding_well_metrics: List[PacBioRunWellMetrics] = [
            well for well in wells if well.pac_bio_run_name == entry.run_name
        ]

        assert [well.label for well in entry.wells] == [
            well.well_label for well in corresponding_well_metrics
        ]

        # Remove them from the original list to make sure there are no duplicates.
        for well in corresponding_well_metrics:
            wells.remove(well)

    # If there are no duplicates then the starting list of wells should be empty.
    assert len(wells) == 0


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
    qcdb_test_session, mlwhdb_test_session, filtered_inbox_data
):
    """Test lang_qc.endpoints.get_well_metrics_from_qc_states function."""
    # Passing an empty list should return an empty list
    assert get_well_metrics_from_qc_states([], mlwhdb_test_session) == []

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
