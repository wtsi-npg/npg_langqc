from sqlalchemy import select

from lang_qc.db.mlwh_schema import PacBioRunWellMetrics

"""Tests for custom and customised ORM methods"""


def test_pac_bio_well_metrics_repr(mlwhdb_test_session, mlwhdb_load_runs):
    id1 = "cf18bd66e0f0895ea728c1d08103c62d3de8a57a5f879cee45f7b0acc028aa61"
    id2 = "513c674f489b106c6af716dd0d210826ff03b7648d50888839c3722ca1b10dbf"
    data = {
        id1: f"pac_bio_run_name=TRACTION-RUN-92, well_label=A1, id_pac_bio_product={id1}",
        id2: f"pac_bio_run_name=TRACTION-RUN-1140, well_label=A1, plate_number=2, id_pac_bio_product={id2}",
    }

    for id in data.keys():
        query = select(PacBioRunWellMetrics).where(
            PacBioRunWellMetrics.id_pac_bio_product == id
        )
        db_row = mlwhdb_test_session.execute(query).scalar_one()
        expected_string = "lang_qc.db.mlwh_schema.PacBioRunWellMetrics: " + data[id]
        assert db_row.__repr__() == expected_string
        assert str(db_row) == expected_string
