from fastapi.testclient import TestClient
from sqlalchemy import select

# from lang_qc.db.mlwh_schema import PacBioRunWellMetrics


def test_well_libraries(test_client: TestClient, mlwhdb_load_runs):
    """Test retrieval of LIMS library data for a well."""

    response = test_client.get(f"/pacbio/wells/malformed/libraries")
    assert response.status_code == 422

    id_product = "aaa8bd66e0f0895ea728c1d08103c62d3de8a57a5f879cee45f7b0acc028aa61"
    response = test_client.get(f"/pacbio/wells/{id_product}/libraries")
    assert response.status_code == 404

    # Partially linked well
    id_product = "26928ba6ec2a00c04dd6c7c68008ec9436e3979a384b9f708dc371c99f272e17"
    response = test_client.get(f"/pacbio/wells/{id_product}/libraries")
    assert response.status_code == 409
    assert response.json()["detail"] == "".join(
        [
            "No LIMS data retrieved for lang_qc.db.mlwh_schema.PacBioRunWellMetrics:",
            " pac_bio_run_name=TRACTION-RUN-1140, well_label=C1, plate_number=2,",
            " id_pac_bio_product=26928ba6ec2a00c04dd6c7c68008ec9436e3979a384b9f708dc371c99f272e17",
            " on account of partially linked or unlinked product data.",
        ]
    )

    # Fully linked well
    id_product = "513c674f489b106c6af716dd0d210826ff03b7648d50888839c3722ca1b10dbf"
    response = test_client.get(f"/pacbio/wells/{id_product}/libraries")
    assert response.status_code == 200
    expected_response = {
        "id_product": "513c674f489b106c6af716dd0d210826ff03b7648d50888839c3722ca1b10dbf",
        "label": "A1",
        "plate_number": 2,
        "run_name": "TRACTION-RUN-1140",
        "run_start_time": "2024-02-23T10:28:12",
        "run_complete_time": "2024-02-25T20:53:05",
        "well_start_time": "2024-02-24T14:25:12",
        "well_complete_time": "2024-02-26T00:27:52",
        "run_status": "Complete",
        "well_status": "Complete",
        "instrument_name": "84093",
        "instrument_type": "Revio",
        "qc_state": None,
        "libraries": [
            {
                "study_id": "5901",
                "study_name": "DTOL_Darwin Tree of Life",
                "sample_id": "9478726",
                "sample_name": "DTOL14523243",
                "tag_sequence": ["ATCTGCACGTGAGTAT"],
                "library_type": "Pacbio_HiFi",
                "pool_name": "TRAC-2-7677",
            },
            {
                "study_id": "5901",
                "study_name": "DTOL_Darwin Tree of Life",
                "sample_id": "9518398",
                "sample_name": "DTOL14180244",
                "tag_sequence": ["ATGTACTAGTGAGTAT"],
                "library_type": "Pacbio_HiFi",
                "pool_name": "TRAC-2-7677",
            },
        ],
    }

    assert response.json() == expected_response
