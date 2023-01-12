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

from tests.fixtures.inbox_data import inbox_data


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
