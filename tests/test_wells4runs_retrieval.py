import pytest

from lang_qc.db.helper.wells import (
    EmptyListOfRunNamesError,
    PacBioPagedWellsFactoryLite,
)
from lang_qc.models.pacbio.well import PacBioPagedWellsLite
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
