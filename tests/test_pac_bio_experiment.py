import pytest
from sqlalchemy import select

from lang_qc.db.mlwh_schema import PacBioRun
from lang_qc.models.pacbio.experiment import PacBioExperiment, PacBioLibrary


def test_creating_library_object(mlwhdb_test_session, mlwhdb_load_runs):

    l = PacBioLibrary(
        study_id="1",
        sample_id="1",
        study_name="st_name",
        sample_name="sa_name",
        tag_sequence=[],
    )
    assert l.study_id == "1"


def test_creating_experiment_object(mlwhdb_test_session, mlwhdb_load_runs):

    run_name = "TRACTION-RUN-92"
    # Four wells, D1 has 40 samples, the rest have one sample each.

    query = (
        select(PacBioRun)
        .where(PacBioRun.pac_bio_run_name == run_name)
        .where(PacBioRun.well_label == "A1")
    )
    well_row = mlwhdb_test_session.execute(query).scalars().one()

    with pytest.raises(Exception, match=r"Empty db_libraries list is not allowed."):
        PacBioExperiment(db_libraries=[])

    with pytest.raises(ValueError, match=r"None db_library value is not allowed."):
        PacBioExperiment(db_libraries=[well_row, None])

    lims = PacBioExperiment(db_libraries=[well_row])
    assert lims.num_samples == 1
    assert lims.study_id == ["6457"]
    assert lims.study_name == "Tree of Life - ASG"
    assert lims.sample_id == "7880641"
    assert lims.sample_name == "TOL_ASG12404704"
    assert lims.library_type == ["PacBio_Ultra_Low_Input"]
    assert lims.tag_sequence == []
    assert lims.pool_name == "TRAC-2-506"

    query = (
        select(PacBioRun)
        .where(PacBioRun.pac_bio_run_name == run_name)
        .where(PacBioRun.well_label == "C1")
    )
    well_row = mlwhdb_test_session.execute(query).scalars().one()

    lims = PacBioExperiment(db_libraries=[well_row])
    assert lims.num_samples == 1
    assert lims.study_id == ["5901"]
    assert lims.study_name == "DTOL_Darwin Tree of Life"
    assert lims.sample_id == "7793103"
    assert lims.sample_name == "DTOL12273960"
    assert lims.library_type == ["PacBio_Ultra_Low_Input"]
    assert lims.tag_sequence == ["GATATATATGTGTGTAT"]
    assert lims.pool_name == "TRAC-2-506"

    query = (
        select(PacBioRun)
        .where(PacBioRun.pac_bio_run_name == run_name)
        .where(PacBioRun.well_label == "D1")
    )
    well_rows = mlwhdb_test_session.execute(query).scalars().all()

    lims = PacBioExperiment(db_libraries=well_rows)
    assert lims.num_samples == 40
    assert lims.study_id == ["7069"]
    assert lims.study_name == "Alternative Enzymes 2022 microbial genomes"
    assert lims.sample_id is None
    assert lims.sample_name is None
    assert lims.library_type == ["Pacbio_HiFi_mplx"]
    assert lims.tag_sequence == []
    assert lims.pool_name == "TRAC-2-533"

    query = (
        select(PacBioRun)
        .where(PacBioRun.pac_bio_run_name == run_name)
        .where(PacBioRun.well_label != "D1")
    )
    well_rows = mlwhdb_test_session.execute(query).scalars().all()

    lims = PacBioExperiment(db_libraries=well_rows)
    assert lims.num_samples == 3
    assert lims.study_id == ["5901", "6457"]
    assert lims.study_name is None
    assert lims.sample_id is None
    assert lims.sample_name is None
    assert lims.library_type == ["PacBio_Ultra_Low_Input"]
    assert lims.tag_sequence == []
    assert lims.pool_name == "TRAC-2-506"

    query = (
        select(PacBioRun)
        .where(PacBioRun.pac_bio_run_name == run_name)
        .where(PacBioRun.well_label != "C1")
    )
    well_rows = mlwhdb_test_session.execute(query).scalars().all()

    with pytest.raises(ValueError, match=r"Multiple pool names."):
        PacBioExperiment(db_libraries=well_rows)

    for row in well_rows:
        row.pac_bio_library_tube_barcode = "AXCTYW"
    mlwhdb_test_session.commit()

    lims = PacBioExperiment(db_libraries=well_rows)
    assert lims.num_samples == 42
    assert lims.study_id == ["6457", "7069"]
    assert lims.study_name is None
    assert lims.sample_id is None
    assert lims.sample_name is None
    assert lims.library_type == ["PacBio_Ultra_Low_Input", "Pacbio_HiFi_mplx"]
    assert lims.tag_sequence == []
