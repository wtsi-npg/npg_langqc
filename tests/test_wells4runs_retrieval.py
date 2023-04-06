import pytest

from lang_qc.db.helper.wells import PacBioPagedWellsFactoryLite
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

    paged_wells_obj = factory.create_for_runs([])
    assert isinstance(paged_wells_obj, PacBioPagedWellsLite)
    assert paged_wells_obj.page_size == 10
    assert paged_wells_obj.page_number == 1
    assert paged_wells_obj.wells == []


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
    assert isinstance(paged_wells_obj, PacBioPagedWellsLite)
    assert paged_wells_obj.page_size == 5
    assert paged_wells_obj.page_number == 3
    assert paged_wells_obj.wells == []
