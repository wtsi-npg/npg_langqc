import pytest

from lang_qc.db.helper.wells import (
    EmptyListOfRunNamesError,
    PacBioPagedWellsFactoryLite,
)
from lang_qc.models.pacbio.well import PacBioPagedWellsLite, PacBioWell
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_empty_list_input(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

    factory = PacBioPagedWellsFactoryLite(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
    )
    with pytest.raises(
        EmptyListOfRunNamesError, match=r"List of run names cannot be empty"
    ):
        factory.create_for_runs([])


def test_unknown_run_input(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

    factory = PacBioPagedWellsFactoryLite(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=5,
        page_number=1,
    )
    paged_wells_obj = factory.create_for_runs(["some run"])
    assert isinstance(paged_wells_obj, PacBioPagedWellsLite)
    assert paged_wells_obj.total_number_of_items == 0
    assert paged_wells_obj.page_size == 5
    assert paged_wells_obj.page_number == 1
    assert paged_wells_obj.wells == []

    factory = PacBioPagedWellsFactoryLite(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=5,
        page_number=3,
    )
    paged_wells_obj = factory.create_for_runs(["some run", "other run"])
    assert paged_wells_obj.total_number_of_items == 0
    assert paged_wells_obj.page_size == 5
    assert paged_wells_obj.page_number == 3
    assert paged_wells_obj.wells == []

    factory = PacBioPagedWellsFactoryLite(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=5,
        page_number=1,
    )
    paged_wells_obj = factory.create_for_runs(["some run", "TRACTION_RUN_1"])
    assert paged_wells_obj.total_number_of_items == 4
    assert paged_wells_obj.page_size == 5
    assert paged_wells_obj.page_number == 1
    assert len(paged_wells_obj.wells) == 4


def test_known_runs_input(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

    factory = PacBioPagedWellsFactoryLite(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=5,
        page_number=1,
    )
    paged_wells_obj = factory.create_for_runs(["TRACTION_RUN_1"])
    assert isinstance(paged_wells_obj, PacBioPagedWellsLite)
    assert paged_wells_obj.total_number_of_items == 4
    assert paged_wells_obj.page_size == 5
    assert paged_wells_obj.page_number == 1

    wells = paged_wells_obj.wells
    assert len(wells) == 4
    object_type_set = {type(well) for well in wells}
    assert object_type_set == {PacBioWell}
    run_name_set = {well.run_name for well in wells}
    assert run_name_set == {"TRACTION_RUN_1"}
    label_list = [well.label for well in wells]
    assert label_list == ["A1", "B1", "C1", "D1"]

    qc_states = [well.qc_state.qc_state for well in wells]
    expected_qc_states = ["Claimed", "On hold", "Claimed", "On hold"]
    assert qc_states == expected_qc_states

    factory = PacBioPagedWellsFactoryLite(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
    )
    paged_wells_obj = factory.create_for_runs(["TRACTION_RUN_1", "TRACTION_RUN_3"])
    assert isinstance(paged_wells_obj, PacBioPagedWellsLite)
    assert paged_wells_obj.total_number_of_items == 6
    assert paged_wells_obj.page_size == 10
    assert paged_wells_obj.page_number == 1

    wells = paged_wells_obj.wells
    assert len(wells) == 6
    object_type_set = {type(well) for well in wells}
    assert object_type_set == {PacBioWell}
    run_names = [well.run_name for well in wells]
    assert run_names == 4 * ["TRACTION_RUN_1"] + 2 * ["TRACTION_RUN_3"]
    label_list = [well.label for well in wells]
    assert label_list == ["A1", "B1", "C1", "D1", "A1", "B1"]

    qc_state_objs = [well.qc_state for well in wells]
    assert qc_state_objs[-1] is None
    assert qc_state_objs[-2] is None
    qc_state_objs = qc_state_objs[:4]
    qc_states = [obj.qc_state for obj in qc_state_objs]
    assert qc_states == expected_qc_states
