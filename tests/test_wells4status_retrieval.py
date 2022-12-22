import pytest

from lang_qc.db.helper.wells import PacBioPagedWellsFactory
from lang_qc.db.qc_schema import QcState
from lang_qc.models.pacbio.well import PacBioPagedWells
from lang_qc.models.qc_flow_status import QcFlowStatusEnum
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_query(qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval):

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
        qc_flow_status=QcFlowStatusEnum.ON_HOLD,
    )
    query = factory._build_query4status()
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
        assert (
            state.date_updated.isoformat(sep=" ", timespec="seconds")
            == update_dates[index]
        )

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
        qc_flow_status=QcFlowStatusEnum.IN_PROGRESS,
    )
    query = factory._build_query4status()
    states = qcdb_test_session.execute(query).scalars().all()
    expected_data = [
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
    for index in range(9):
        state = states[index]
        assert isinstance(state, QcState)
        assert state.is_preliminary == 1
        assert state.qc_type.qc_type == "sequencing"
        assert state.qc_state_dict.state == expected_data[index][0]
        assert (
            state.date_updated.isoformat(sep=" ", timespec="seconds")
            == expected_data[index][1]
        )

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
        qc_flow_status=QcFlowStatusEnum.QC_COMPLETE,
    )
    query = factory._build_query4status()
    print(str(query))
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
    for index in range(4):
        state = states[index]
        assert isinstance(state, QcState)
        assert state.is_preliminary == 0
        assert state.qc_type.qc_type == "sequencing"
        assert state.qc_state_dict.state == expected_data[index][0]
        assert (
            state.date_updated.isoformat(sep=" ", timespec="seconds")
            == expected_data[index][1]
        )


def test_inbox_retrieval(qcdb_test_session, mlwhdb_test_session):

    factory = PacBioPagedWellsFactory(
        qcdb_session=qcdb_test_session,
        mlwh_session=mlwhdb_test_session,
        page_size=10,
        page_number=1,
        qc_flow_status=QcFlowStatusEnum.INBOX,
    )
    with pytest.raises(Exception, match=r"Not implemented"):
        factory.create()


def test_paged_retrieval(
    qcdb_test_session, mlwhdb_test_session, load_data4well_retrieval
):

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
            qc_flow_status=status,
        )
        paged_wells = factory.create()
        assert isinstance(paged_wells, PacBioPagedWells)
        assert paged_wells.page_size == 10
        assert paged_wells.page_number == 1
        assert paged_wells.qc_flow_status == status
        total_number_of_items = paged_wells.total_number_of_items
        # assert total_number_of_items != 0
        # assert len(paged_wells.wells) != 0

        factory = PacBioPagedWellsFactory(
            qcdb_session=qcdb_test_session,
            mlwh_session=mlwhdb_test_session,
            page_size=2,
            page_number=10,
            qc_flow_status=status,
        )
        paged_wells = factory.create()
        assert isinstance(paged_wells, PacBioPagedWells)
        assert paged_wells.page_size == 2
        assert paged_wells.page_number == 10
        assert paged_wells.qc_flow_status == status
        assert paged_wells.total_number_of_items == total_number_of_items
        assert len(paged_wells.wells) == 0

        factory = PacBioPagedWellsFactory(
            qcdb_session=qcdb_test_session,
            mlwh_session=mlwhdb_test_session,
            page_size=1,
            page_number=1,
            qc_flow_status=status,
        )
        paged_wells = factory.create()
        assert isinstance(paged_wells, PacBioPagedWells)
        assert paged_wells.page_size == 1
        assert paged_wells.page_number == 1
        assert paged_wells.qc_flow_status == status
        assert paged_wells.total_number_of_items == total_number_of_items
        # assert len(paged_wells.wells) == 1

        factory = PacBioPagedWellsFactory(
            qcdb_session=qcdb_test_session,
            mlwh_session=mlwhdb_test_session,
            page_size=1,
            page_number=2,
            qc_flow_status=status,
        )
        paged_wells = factory.create()
        assert isinstance(paged_wells, PacBioPagedWells)
        assert paged_wells.page_size == 1
        assert paged_wells.page_number == 2
        assert paged_wells.qc_flow_status == status
        assert paged_wells.total_number_of_items == total_number_of_items
        # assert len(paged_wells.wells) == 1
