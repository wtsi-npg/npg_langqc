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

from fastapi.testclient import TestClient

from tests.fixtures.inbox_data import filtered_inbox_data, inbox_data


def test_incorrect_filter(test_client: TestClient):
    """Expect a 422 response when an incorrect filter is given."""

    response = test_client.get("/pacbio/wells?qc_status=thisdoesntexist")
    assert response.status_code == 422


def test_qc_complete_filter(test_client: TestClient, filtered_inbox_data):
    """Test passing `qc_complete` filter."""

    response = test_client.get("/pacbio/wells?qc_status=qc_complete")
    assert response.status_code == 200
    assert len(response.json()) == 1
    run = response.json()[0]
    assert run["run_name"] == "MARATHON"
    assert len(run["wells"]) == 1
    assert run["wells"][0]["label"] == "A2"
    assert not run["wells"][0]["qc_status"]["is_preliminary"]
    assert run["wells"][0]["qc_status"]["qc_state"] == "Passed"
