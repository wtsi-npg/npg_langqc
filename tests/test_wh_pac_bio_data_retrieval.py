from datetime import datetime, timedelta

import pytest
from ml_warehouse.schema import PacBioRunWellMetrics
from sqlalchemy import select

from lang_qc.db.helper.wells import WellWh
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_completed_wells_retrieval(mlwhdb_test_session, load_data4well_retrieval):

    # Not all wells of the listed here runs end up in the inbox.
    expected = [
        ["TRACTION_RUN_1", "A1"],
        ["TRACTION_RUN_1", "B1"],
        ["TRACTION_RUN_1", "C1"],
        ["TRACTION_RUN_1", "D1"],
        ["TRACTION_RUN_4", "A1"],
        ["TRACTION_RUN_4", "B1"],
        ["TRACTION_RUN_4", "C1"],
        ["TRACTION_RUN_4", "D1"],
        ["TRACTION_RUN_3", "A1"],
        ["TRACTION_RUN_3", "B1"],
        ["TRACTION_RUN_10", "A1"],
        ["TRACTION_RUN_10", "B1"],
        ["TRACTION_RUN_10", "C1"],
        ["TRACTION_RUN_12", "A1"],
    ]

    # The inbox selection is for recent data. Runs that should not appear
    # in the inbox should have their completion dates reset to be outside
    # of the time window for the inbox.
    run_names = {e[0] for e in expected}  # get a unique set of run names
    wells_to_update = (
        mlwhdb_test_session.execute(
            select(PacBioRunWellMetrics).where(
                PacBioRunWellMetrics.pac_bio_run_name.notin_(run_names)
            )
        )
        .scalars()
        .all()
    )
    time = datetime.now() - timedelta(days=40)
    for row in wells_to_update:
        if row.well_complete is not None:
            row.well_complete = time
            row.run_complete = time
            mlwhdb_test_session.add(row)
    mlwhdb_test_session.commit()

    retriever = WellWh(session=mlwhdb_test_session)
    wells = retriever.recent_completed_wells()
    wells_ids = [[well.pac_bio_run_name, well.well_label] for well in wells]
    assert len(wells_ids) == len(expected)
    assert wells_ids == expected


def test_well_metrics_retrieval(mlwhdb_test_session, load_data4well_retrieval):

    wm = WellWh(session=mlwhdb_test_session)
    assert wm.get_well(run_name="UNKNOWN", well_label="A1") is None
    assert wm.well_exists(run_name="UNKNOWN", well_label="A1") is False

    wm = WellWh(session=mlwhdb_test_session)
    well = wm.get_well(run_name="TRACTION_RUN_12", well_label="A1")
    assert well.pac_bio_run_name == "TRACTION_RUN_12"
    assert well.well_label == "A1"
    assert well.run_status == "None"
    assert well.well_status == "Complete"
    assert well.ccs_execution_mode == "OffInstrument"
    assert well.polymerase_num_reads == 3339714
    assert well.hifi_num_reads == 2226107
    assert wm.well_exists(run_name="TRACTION_RUN_12", well_label="A1") is True


def test_wells_in_runs_retrieval(mlwhdb_test_session, load_data4well_retrieval):

    wm = WellWh(session=mlwhdb_test_session)
    assert wm.get_wells_in_runs([]) == []
    assert wm.get_wells_in_runs(["some name"]) == []
