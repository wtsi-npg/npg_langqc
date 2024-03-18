from npg_id_generation.pac_bio import PacBioEntity
from sqlalchemy.orm import Session

from lang_qc.db.helper.qc import get_qc_states_by_id_product_list
from lang_qc.db.helper.wells import WellWh
from lang_qc.db.mlwh_schema import PacBioRunWellMetrics
from lang_qc.models.pacbio.well import PacBioWellFull, PacBioWellSummary
from tests.conftest import compare_dates
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users

yaml_is_loaded: bool = False


def _prepare_data(
    mlwhdb_session: Session,
    qcdb_session: Session,
    run_name: str,
    well_label: str,
    plate_number: int = None,
):
    """Returns mlwh data for one well.

    Returns a tuple of an mlwh db row and QC state model for one well.
    """

    id_product = PacBioEntity(
        run_name=run_name, well_label=well_label, plate_number=plate_number
    ).hash_product_id()
    well_row = WellWh(session=mlwhdb_session).get_mlwh_well_by_product_id(id_product)

    qc_state = None
    qc_states = get_qc_states_by_id_product_list(
        session=qcdb_session,
        ids=[id_product],
        sequencing_outcomes_only=True,
    )
    if id_product in qc_states:
        qc_state = qc_states[id_product][0]

    return (well_row, qc_state)


def _examine_well_model_a1(pb_well: PacBioRunWellMetrics, id_product: str):

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
    assert pb_well.instrument_name == "64222E"
    assert pb_well.instrument_type == "Sequel2e"


def _examine_well_model_b1(pb_well: PacBioRunWellMetrics, id_product: str):

    assert pb_well.id_product == id_product
    assert pb_well.run_name == "TRACTION_RUN_1"
    assert pb_well.label == "B1"
    assert pb_well.plate_number is None
    assert pb_well.run_status == "Complete"
    assert pb_well.well_status == "Complete"
    assert pb_well.qc_state is not None
    assert pb_well.instrument_name == "64016"
    assert pb_well.instrument_type == "Sequel2"


def _examine_well_model_c1(pb_well: PacBioRunWellMetrics, id_product: str):

    assert pb_well.id_product == id_product
    assert pb_well.run_name == "TRACTION_RUN_10"
    assert pb_well.label == "C1"
    assert pb_well.plate_number == 1
    assert pb_well.well_status == "Complete"
    assert pb_well.run_status == "Aborted"
    assert pb_well.qc_state is None
    assert pb_well.instrument_name == "1234"
    assert pb_well.instrument_type == "Revio"


def test_create_full_model(
    mlwhdb_test_session, qcdb_test_session, load_data4well_retrieval, mlwhdb_load_runs
):
    # Full mlwh data, no data in the lang_qc database.
    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION-RUN-92", "A1"
    )
    pb_well = PacBioWellFull(db_well=well_row)
    _examine_well_model_a1(pb_well, well_row.id_pac_bio_product)
    assert pb_well.metrics is not None
    assert pb_well.experiment_tracking is not None

    # Only run_well mlwh data (no products), and data in the lang_qc database.
    # Very sketchy mlwh qc metrics data.
    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION_RUN_1", "B1"
    )
    pb_well = PacBioWellFull(db_well=well_row, qc_state=qc_state)
    _examine_well_model_b1(pb_well, well_row.id_pac_bio_product)
    assert pb_well.metrics is not None
    assert pb_well.experiment_tracking is None

    # Only run_well mlwh data (no products), no data in the lang_qc database.
    # Very sketchy mlwh qc metrics data.
    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION_RUN_10", "C1"
    )
    pb_well = PacBioWellFull(db_well=well_row, qc_state=None)
    _examine_well_model_c1(pb_well, well_row.id_pac_bio_product)
    assert pb_well.metrics is not None
    assert pb_well.experiment_tracking is None


def test_create_summary_model(
    mlwhdb_test_session, qcdb_test_session, load_data4well_retrieval, mlwhdb_load_runs
):
    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION-RUN-92", "A1"
    )
    pb_well = PacBioWellSummary(db_well=well_row)
    _examine_well_model_a1(pb_well, well_row.id_pac_bio_product)
    assert pb_well.study_names == ["Tree of Life - ASG"]

    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION_RUN_1", "B1"
    )
    pb_well = PacBioWellSummary(db_well=well_row, qc_state=qc_state)
    _examine_well_model_b1(pb_well, well_row.id_pac_bio_product)
    assert pb_well.study_names == []

    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION_RUN_10", "C1"
    )
    pb_well = PacBioWellFull(db_well=well_row, qc_state=None)
    _examine_well_model_c1(pb_well, well_row.id_pac_bio_product)


def test_create_summary_model_study_info(
    mlwhdb_test_session, qcdb_test_session, load_data4well_retrieval, mlwhdb_load_runs
):
    # Well with two samples, none is linked to LIMS
    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION-RUN-1140", "A1", 1
    )
    pb_well = PacBioWellSummary(db_well=well_row)
    assert pb_well.study_names == []

    # Fully linked wells with one sample
    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION-RUN-1162", "C1"
    )
    pb_well = PacBioWellSummary(db_well=well_row)
    assert pb_well.study_names == ["DTOL_Darwin R&D"]

    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION-RUN-1162", "D1", 1
    )
    pb_well = PacBioWellSummary(db_well=well_row)
    assert pb_well.study_names == ["DTOL_Darwin Tree of Life"]

    # A fully linked well with multiple samples, all belonging to the same study
    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION-RUN-1140", "B1", 1
    )
    pb_well = PacBioWellSummary(db_well=well_row)
    assert pb_well.study_names == ["DTOL_Darwin Tree of Life"]

    # A fully linked well with multiple samples, which belong to two studies
    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION-RUN-1140", "D1", 1
    )
    pb_well = PacBioWellSummary(db_well=well_row)
    assert pb_well.study_names == [
        "DTOL_Darwin Tree of Life",
        "ToL_Blaxter_ Reference Genomes_ DNA",
    ]

    # A partially linked well with three samples, which belong to two studies.
    # The LIMS link for one of the samples is deleted so that two other samples
    # belong to the same study.
    (well_row, qc_state) = _prepare_data(
        mlwhdb_test_session, qcdb_test_session, "TRACTION-RUN-1140", "C1", 2
    )
    pb_well = PacBioWellSummary(db_well=well_row)
    assert pb_well.study_names == []
