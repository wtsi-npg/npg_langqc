from npg_id_generation.pac_bio import PacBioEntity
from sqlalchemy import select

from lang_qc.db.helper.well import well_seq_product_find_or_create
from lang_qc.db.mlwh_schema import PacBioRunWellMetrics
from lang_qc.db.qc_schema import SeqProduct
from tests.fixtures.well_data import load_data4well_retrieval, load_dicts_and_users


def test_find_well_record(
    mlwhdb_test_session, qcdb_test_session, load_data4well_retrieval
):

    id = PacBioEntity(
        run_name="TRACTION_RUN_2", well_label="A1", plate_number=1
    ).hash_product_id()
    # Test fixtures should have created this record.
    sp = qcdb_test_session.execute(
        select(SeqProduct).where(SeqProduct.id_product == id)
    ).scalar_one()
    mlwh_row = mlwhdb_test_session.execute(
        select(PacBioRunWellMetrics).where(
            PacBioRunWellMetrics.id_pac_bio_product == id
        )
    ).scalar_one()

    seq_product = well_seq_product_find_or_create(qcdb_test_session, mlwh_row)
    assert seq_product.id_product == id
    assert seq_product.id_seq_product == sp.id_seq_product


def test_create_well_record(
    mlwhdb_test_session, qcdb_test_session, load_data4well_retrieval
):

    # Plate number is defined.
    id = PacBioEntity(
        run_name="TRACTION_RUN_15", well_label="A1", plate_number=1
    ).hash_product_id()
    mlwh_row = mlwhdb_test_session.execute(
        select(PacBioRunWellMetrics).where(
            PacBioRunWellMetrics.id_pac_bio_product == id
        )
    ).scalar_one()
    sp = (
        qcdb_test_session.execute(select(SeqProduct).where(SeqProduct.id_product == id))
        .scalars()
        .one_or_none()
    )
    assert sp is None

    seq_product = well_seq_product_find_or_create(qcdb_test_session, mlwh_row)
    assert seq_product.id_product == id
    assert seq_product.seq_platform.name == "PacBio"
    sub_products = seq_product.sub_products
    assert len(sub_products) == 1
    sub_product = sub_products[0]
    assert sub_product.sub_product_attr.attr_name == "run_name"
    assert sub_product.value_attr_one == "TRACTION_RUN_15"
    assert sub_product.sub_product_attr_.attr_name == "well_label"
    assert sub_product.value_attr_two == "A1"
    assert sub_product.sub_product_attr__.attr_name == "plate_number"
    assert sub_product.value_attr_three == "1"

    # Plate number is undefined.
    id = PacBioEntity(run_name="TRACTION_RUN_14", well_label="B1").hash_product_id()
    mlwh_row = mlwhdb_test_session.execute(
        select(PacBioRunWellMetrics).where(
            PacBioRunWellMetrics.id_pac_bio_product == id
        )
    ).scalar_one()
    sp = (
        qcdb_test_session.execute(select(SeqProduct).where(SeqProduct.id_product == id))
        .scalars()
        .one_or_none()
    )
    assert sp is None

    seq_product = well_seq_product_find_or_create(qcdb_test_session, mlwh_row)
    assert seq_product.id_product == id
    assert seq_product.seq_platform.name == "PacBio"
    sub_products = seq_product.sub_products
    assert len(sub_products) == 1
    sub_product = sub_products[0]
    assert sub_product.sub_product_attr.attr_name == "run_name"
    assert sub_product.value_attr_one == "TRACTION_RUN_14"
    assert sub_product.sub_product_attr_.attr_name == "well_label"
    assert sub_product.value_attr_two == "B1"
    assert sub_product.sub_product_attr__.attr_name == "plate_number"
    assert sub_product.value_attr_three is None
