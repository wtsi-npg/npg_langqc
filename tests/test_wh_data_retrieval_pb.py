from datetime import datetime, timedelta

import pytest
from npg_id_generation.pac_bio import PacBioEntity
from sqlalchemy import select

from lang_qc.db.helper.wells import EmptyListOfRunNamesError, WellWh
from lang_qc.db.mlwh_schema import PacBioRunWellMetrics
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

    id_product = PacBioEntity(run_name="UNKNOWN", well_label="A1").hash_product_id()
    assert wm.get_mlwh_well_by_product_id(id_product) is None

    id_product = PacBioEntity(
        run_name="TRACTION_RUN_12", well_label="A1"
    ).hash_product_id()
    well = wm.get_mlwh_well_by_product_id(id_product)
    assert well.id_pac_bio_product == id_product
    assert well.pac_bio_run_name == "TRACTION_RUN_12"
    assert well.well_label == "A1"
    assert well.run_status == "None"
    assert well.well_status == "Complete"
    assert well.ccs_execution_mode == "OffInstrument"
    assert well.polymerase_num_reads == 3339714
    assert well.hifi_num_reads == 2226107


def test_wells_in_runs_retrieval_boundary_cases(
    mlwhdb_test_session, load_data4well_retrieval
):

    wm = WellWh(session=mlwhdb_test_session)
    with pytest.raises(
        EmptyListOfRunNamesError, match=r"List of run names cannot be empty"
    ):
        wm.get_wells_in_runs([])
    assert wm.get_wells_in_runs(["some name"]) == []


def test_wells_in_runs_retrieval(mlwhdb_test_session, load_data4well_retrieval):

    wm = WellWh(session=mlwhdb_test_session)

    wells = wm.get_wells_in_runs(["TRACTION_RUN_1"])
    assert len(wells) == 4
    run_name_set = {row.pac_bio_run_name for row in wells}
    assert run_name_set == {"TRACTION_RUN_1"}

    wells = wm.get_wells_in_runs(["some run", "TRACTION_RUN_1"])
    assert len(wells) == 4
    run_name_set = {row.pac_bio_run_name for row in wells}
    assert run_name_set == {"TRACTION_RUN_1"}

    wells = wm.get_wells_in_runs(["TRACTION_RUN_2", "TRACTION_RUN_1"])
    assert len(wells) == 12

    # Test that the rows are correctly sorted
    run_names = [row.pac_bio_run_name for row in wells]

    for i in range(0, 4):
        assert run_names[i] == "TRACTION_RUN_1"
    for i in range(4, 12):
        assert run_names[i] == "TRACTION_RUN_2"

    plates_and_labels = [(row.well_label, row.plate_number) for row in wells]
    expected_labels = 3 * ["A1", "B1", "C1", "D1"]
    expected_plate_numbers = 4 * [None] + 4 * [1] + 4 * [2]
    for i in range(0, 12):
        assert plates_and_labels[i][0] == expected_labels[i]
        if i < 4:
            assert plates_and_labels[i][1] is None
        else:
            assert plates_and_labels[i][1] == expected_plate_numbers[i]
