import pytest
from npg_id_generation.pac_bio import PacBioEntity

from lang_qc.db.helper.wells import PacBioPagedWellsFactory, RunNotFoundError
from lang_qc.db.qc_schema import QcState
from lang_qc.models.pacbio.well import PacBioPagedWells, PacBioWell
from lang_qc.models.qc_flow_status import QcFlowStatusEnum
from lang_qc.models.qc_state import QcState as QcStateModel
from tests.conftest import compare_dates
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_query_for_status(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
    )
    query = factory._build_query4status(QcFlowStatusEnum.ON_HOLD)
    states = qcdb_test_session.execute(query).scalars().all()
    assert len(states) == 2
    # The results should be sorted by the update date in a descending order.
    update_dates = ["2022-12-08 09:15:19", "2022-12-08 07:15:19"]
    for index in (0, 1):
        state = states[index]
        assert isinstance(state, QcState)
        assert state.is_preliminary == 1
        assert state.qc_type.qc_type == "sequencing"
        assert state.qc_state_dict.state == "On hold"
        compare_dates(state.date_updated, update_dates[index])

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
    )
    query = factory._build_query4status(QcFlowStatusEnum.IN_PROGRESS)
    states = qcdb_test_session.execute(query).scalars().all()
    expected_data = [
        ["Failed", "2022-02-15 10:42:33"],
        ["Claimed", "2022-02-15 10:42:34"],
        ["Claimed", "2022-12-07 07:15:19"],
        ["Claimed", "2022-12-07 09:15:19"],
        ["Failed, Instrument", "2022-12-07 15:13:56"],
        ["Claimed", "2022-12-08 08:15:19"],
        ["Failed, SMRT cell", "2022-12-08 18:14:56"],
        ["Failed", "2022-12-12 16:02:57"],
        ["Aborted", "2022-12-15 10:42:33"],
        ["Aborted", "2022-12-15 11:42:33"],
        ["Passed", "2022-12-22 16:21:06"],
    ]
    # The results should be sorted by the update date in a descending order.
    expected_data.reverse()  # in place
    assert len(states) == len(expected_data)
    for state, expected_state in zip(states, expected_data):
        assert isinstance(state, QcState)
        assert state.is_preliminary == 1
        assert state.qc_type.qc_type == "sequencing"
        assert state.qc_state_dict.state == expected_state[0]
        compare_dates(state.date_updated, expected_state[1])

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
    )
    query = factory._build_query4status(QcFlowStatusEnum.QC_COMPLETE)
    states = qcdb_test_session.execute(query).scalars().all()
    expected_data = [
        ["Failed, SMRT cell", "2022-12-07 15:23:56"],
        ["Failed, Instrument", "2022-12-08 15:18:56"],
        ["Failed", "2022-12-12 12:02:57"],
        ["Passed", "2022-12-21 14:21:06"],
    ]
    # The results should be sorted by the update date in a descending order.
    expected_data.reverse()  # in place
    assert len(states) == len(expected_data)
    for state, expected_state in zip(states, expected_data):
        assert isinstance(state, QcState)
        assert state.is_preliminary == 0
        assert state.qc_type.qc_type == "sequencing"
        assert state.qc_state_dict.state == expected_state[0]
        compare_dates(state.date_updated, expected_state[1])


def test_inbox_wells_retrieval(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

    # To understand how the test db records for inbox wells are set up,
    # please see the comment at the beginning of the _update_timestamps4inbox()
    # function in tests.fixtures.well_data

    status = QcFlowStatusEnum.INBOX

    paged_wells = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
    ).create_for_qc_status(status)
    assert isinstance(paged_wells, PacBioPagedWells)
    assert paged_wells.page_size == 10
    assert paged_wells.page_number == 1
    assert paged_wells.total_number_of_items == 8
    assert len(paged_wells.wells) == 8

    paged_wells = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=2,
    ).create_for_qc_status(status)
    assert isinstance(paged_wells, PacBioPagedWells)
    assert paged_wells.page_size == 10
    assert paged_wells.page_number == 2
    assert paged_wells.total_number_of_items == 8
    assert len(paged_wells.wells) == 0

    paged_wells = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=3,
        page_number=3,
    ).create_for_qc_status(status)
    assert isinstance(paged_wells, PacBioPagedWells)
    assert paged_wells.page_size == 3
    assert paged_wells.page_number == 3
    assert paged_wells.total_number_of_items == 8
    assert len(paged_wells.wells) == 2

    # The dates for this well had been amended prior to loading to the db,
    # so we cannot hardcode expected dates.
    mlwh_data = load_data4well_retrieval

    well = paged_wells.wells[0]
    assert isinstance(well, PacBioWell)
    assert well.run_name == "TRACTION_RUN_10"
    assert well.label == "C1"
    assert well.qc_state is None
    [well_fixture] = [
        f for f in mlwh_data if (f[0] == "TRACTION_RUN_10" and f[1] == "C1")
    ]
    compare_dates(well.run_start_time, well_fixture[2])
    compare_dates(well.run_complete_time, well_fixture[3])
    compare_dates(well.well_start_time, well_fixture[4])
    compare_dates(well.well_complete_time, well_fixture[5])

    well = paged_wells.wells[1]
    assert isinstance(well, PacBioWell)
    assert well.run_name == "TRACTION_RUN_12"
    assert well.label == "A1"
    assert well.qc_state is None
    [well_fixture] = [
        f for f in mlwh_data if (f[0] == "TRACTION_RUN_12" and f[1] == "A1")
    ]
    compare_dates(well.run_start_time, well_fixture[2])
    compare_dates(well.run_complete_time, well_fixture[3])
    compare_dates(well.well_start_time, well_fixture[4])
    compare_dates(well.well_complete_time, well_fixture[5])


def test_paged_retrieval_for_statuses(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

    expected_page_details = {
        QcFlowStatusEnum.IN_PROGRESS.name: 11,
        QcFlowStatusEnum.ON_HOLD.name: 2,
        QcFlowStatusEnum.QC_COMPLETE.name: 4,
    }

    for status in [
        QcFlowStatusEnum.IN_PROGRESS,
        QcFlowStatusEnum.ON_HOLD,
        QcFlowStatusEnum.QC_COMPLETE,
    ]:

        factory = PacBioPagedWellsFactory(
            qcdb_session=qcdb_test_session,
            mlwh_session=mlwhdb_test_session,
            page_size=10,
            page_number=1,
        )
        paged_wells = factory.create_for_qc_status(status)
        assert isinstance(paged_wells, PacBioPagedWells)
        assert paged_wells.page_size == 10
        assert paged_wells.page_number == 1
        total_number_of_items = paged_wells.total_number_of_items
        assert total_number_of_items == expected_page_details[status.name]
        # One QC entity is not in mlwh, hence te number of returned
        # records is returned by one. The number of records that was
        # paged is correct.
        assert (
            len(paged_wells.wells) == total_number_of_items
            if status == "pending"
            else total_number_of_items - 1
        )

        factory = PacBioPagedWellsFactory(
            qcdb_session=qcdb_test_session,
            mlwh_session=mlwhdb_test_session,
            page_size=2,
            page_number=10,
        )
        paged_wells = factory.create_for_qc_status(status)
        assert isinstance(paged_wells, PacBioPagedWells)
        assert paged_wells.page_size == 2
        assert paged_wells.page_number == 10
        assert paged_wells.total_number_of_items == total_number_of_items
        assert len(paged_wells.wells) == 0

        factory = PacBioPagedWellsFactory(
            qcdb_session=qcdb_test_session,
            mlwh_session=mlwhdb_test_session,
            page_size=1,
            page_number=1,
        )
        paged_wells = factory.create_for_qc_status(status)
        assert isinstance(paged_wells, PacBioPagedWells)
        assert paged_wells.page_size == 1
        assert paged_wells.page_number == 1
        assert paged_wells.total_number_of_items == total_number_of_items
        assert len(paged_wells.wells) == 1

        factory = PacBioPagedWellsFactory(
            qcdb_session=qcdb_test_session,
            mlwh_session=mlwhdb_test_session,
            page_size=1,
            page_number=2,
        )
        paged_wells = factory.create_for_qc_status(status)
        assert isinstance(paged_wells, PacBioPagedWells)
        assert paged_wells.page_size == 1
        assert paged_wells.page_number == 2
        assert paged_wells.total_number_of_items == total_number_of_items
        assert len(paged_wells.wells) == 1

        factory = PacBioPagedWellsFactory(
            qcdb_session=qcdb_test_session,
            mlwh_session=mlwhdb_test_session,
            page_size=10,
            page_number=2,
        )
        paged_wells = factory.create_for_qc_status(status)
        assert isinstance(paged_wells, PacBioPagedWells)
        assert paged_wells.page_size == 10
        assert paged_wells.page_number == 2
        assert paged_wells.total_number_of_items == total_number_of_items
        assert len(paged_wells.wells) == (
            1 if status == QcFlowStatusEnum.IN_PROGRESS else 0
        )

    status = QcFlowStatusEnum.QC_COMPLETE
    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=3,
        page_number=2,
    )
    paged_wells = factory.create_for_qc_status(status)
    assert isinstance(paged_wells, PacBioPagedWells)
    assert paged_wells.page_size == 3
    assert paged_wells.page_number == 2
    assert paged_wells.total_number_of_items == 4
    assert len(paged_wells.wells) == 1


def test_fully_retrieved_data_for_statuses(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=5,
        page_number=1,
    )
    paged_wells = factory.create_for_qc_status(QcFlowStatusEnum.QC_COMPLETE)

    well = paged_wells.wells[0]
    assert isinstance(well, PacBioWell)
    assert well.run_name == "TRACTION_RUN_5"
    assert well.label == "B1"
    compare_dates(well.run_start_time, "2022-12-14 11:56:33")
    compare_dates(well.run_complete_time, "2022-12-21 09:20:16")
    compare_dates(well.well_start_time, "2022-12-14 12:06:49")
    compare_dates(well.well_complete_time, "2022-12-15 23:35:44")

    qc_state = well.qc_state
    id = PacBioEntity(run_name=well.run_name, well_label=well.label).hash_product_id()
    assert isinstance(qc_state, QcStateModel)
    assert qc_state.qc_state == "Passed"
    assert qc_state.qc_type == "sequencing"
    assert qc_state.is_preliminary is False
    assert qc_state.outcome == 1
    assert qc_state.id_product == id
    compare_dates(qc_state.date_created, "2022-12-21 14:21:06")
    compare_dates(qc_state.date_updated, "2022-12-21 14:21:06")
    assert qc_state.user == "zx80@example.com"
    assert qc_state.created_by == "LangQC"

    well = paged_wells.wells[3]
    assert isinstance(well, PacBioWell)
    assert well.run_name == "TRACTION_RUN_2"
    assert well.label == "D1"
    compare_dates(well.run_start_time, "2022-12-02 15:11:22")
    compare_dates(well.run_complete_time, "2022-12-09 11:26:27")
    compare_dates(well.well_start_time, "2022-12-06 01:20:31")
    compare_dates(well.well_complete_time, "2022-12-07 14:13:56")

    qc_state = well.qc_state
    id = PacBioEntity(run_name=well.run_name, well_label=well.label).hash_product_id()
    assert isinstance(qc_state, QcStateModel)
    assert qc_state.qc_state == "Failed, SMRT cell"
    assert qc_state.qc_type == "sequencing"
    assert qc_state.is_preliminary is False
    assert qc_state.outcome == 0
    assert qc_state.id_product == id
    compare_dates(qc_state.date_created, "2022-12-07 15:23:56")
    compare_dates(qc_state.date_updated, "2022-12-07 15:23:56")
    assert qc_state.user == "zx80@example.com"
    assert qc_state.created_by == "LangQC"


def test_partially_retrieved_data_for_statuses(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):
    """
    QC for TRACTION_RUN_1 well label E1 is in progress, but the mlwh
    for this entity does not exist. Data for this entity should not
    be retrieved.
    """

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=5,
        page_number=2,
    )
    paged_wells = factory.create_for_qc_status(QcFlowStatusEnum.IN_PROGRESS)
    run_wells = [
        w
        for w in paged_wells.wells
        if (w.run_name == "TRACTION_RUN_1" and w.label == "E1")
    ]
    assert len(run_wells) == 0


def test_unknown_run_name_input(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=5,
        page_number=1,
    )

    with pytest.raises(
        RunNotFoundError, match=r"Metrics data for run 'some run' is not found"
    ):
        factory.create_for_run("some run")


def test_known_run_names_input(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=5,
        page_number=1,
    )
    paged_wells_obj = factory.create_for_run("TRACTION_RUN_1")
    assert isinstance(paged_wells_obj, PacBioPagedWells)
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

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
    )
    paged_wells_obj = factory.create_for_run("TRACTION_RUN_3")
    assert isinstance(paged_wells_obj, PacBioPagedWells)
    assert paged_wells_obj.total_number_of_items == 2
    assert paged_wells_obj.page_size == 10
    assert paged_wells_obj.page_number == 1

    wells = paged_wells_obj.wells
    assert len(wells) == 2
    object_type_set = {type(well) for well in wells}
    assert object_type_set == {PacBioWell}
    run_names = [well.run_name for well in wells]
    assert run_names == 2 * ["TRACTION_RUN_3"]
    label_list = [well.label for well in wells]
    assert label_list == ["A1", "B1"]

    qc_state_objs = [well.qc_state for well in wells]
    assert qc_state_objs[0] is None
    assert qc_state_objs[1] is None
