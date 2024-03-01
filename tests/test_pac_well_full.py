from npg_id_generation.pac_bio import PacBioEntity

from lang_qc.db.helper.wells import WellWh
from lang_qc.models.pacbio.well import PacBioWellFull
from tests.conftest import compare_dates, insert_from_yaml
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_creating_experiment_object(
    mlwhdb_test_session, qcdb_test_session, load_data4well_retrieval
):

    insert_from_yaml(
        mlwhdb_test_session, "tests/data/mlwh_pb_run_92", "lang_qc.db.mlwh_schema"
    )
    helper = WellWh(session=mlwhdb_test_session)

    # Full mlwh data, no data in the lang_qc database.
    id_product = PacBioEntity(
        run_name="TRACTION-RUN-92", well_label="A1"
    ).hash_product_id()
    well_row = helper.get_mlwh_well_by_product_id(id_product)

    pb_well = PacBioWellFull(db_well=well_row, qc_session=qcdb_test_session)
    assert pb_well.id_product == id_product
    assert pb_well.run_name == "TRACTION-RUN-92"
    assert pb_well.label == "A1"
    assert pb_well.plate_number is None
    assert pb_well.qc_state is None
    compare_dates(pb_well.run_start_time, "2022-04-14 12:52:34")
    compare_dates(pb_well.run_complete_time, "2022-04-20 09:16:53")
    compare_dates(pb_well.well_start_time, "2022-04-14 13:02:48")
    compare_dates(pb_well.well_complete_time, "2022-04-16 12:36:21")
    assert pb_well.run_status == "Complete"
    assert pb_well.well_status == "Complete"
    assert pb_well.metrics is not None
    assert pb_well.experiment_tracking is not None
    assert pb_well.instrument_name == "64222E"
    assert pb_well.instrument_type == "Sequel2e"

    # Only run_well mlwh data (no products), and data in the lang_qc database.
    # Very sketchy mlwh qc metrics data
    id_product = PacBioEntity(
        run_name="TRACTION_RUN_1", well_label="B1"
    ).hash_product_id()
    well_row = helper.get_mlwh_well_by_product_id(id_product)

    pb_well = PacBioWellFull(db_well=well_row, qc_session=qcdb_test_session)
    assert pb_well.id_product == id_product
    assert pb_well.run_name == "TRACTION_RUN_1"
    assert pb_well.label == "B1"
    assert pb_well.plate_number is None
    assert pb_well.run_status == "Complete"
    assert pb_well.well_status == "Complete"
    assert pb_well.qc_state is not None
    assert pb_well.metrics is not None
    assert pb_well.experiment_tracking is None
    assert pb_well.instrument_name == "64016"
    assert pb_well.instrument_type == "Sequel2"

    # Only run_well mlwh data (no products), no data in the lang_qc database.
    # Very sketchy mlwh qc metrics data
    id_product = PacBioEntity(
        run_name="TRACTION_RUN_10", well_label="C1"
    ).hash_product_id()
    well_row = helper.get_mlwh_well_by_product_id(id_product)

    pb_well = PacBioWellFull(db_well=well_row, qc_session=qcdb_test_session)
    assert pb_well.id_product == id_product
    assert pb_well.run_name == "TRACTION_RUN_10"
    assert pb_well.label == "C1"
    assert pb_well.plate_number == 1
    assert pb_well.well_status == "Complete"
    assert pb_well.run_status == "Aborted"
    assert pb_well.qc_state is None
    assert pb_well.metrics is not None
    assert pb_well.experiment_tracking is None
    assert pb_well.instrument_name == "1234"
    assert pb_well.instrument_type == "Revio"
