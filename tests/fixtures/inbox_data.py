from datetime import datetime, timedelta

from ml_warehouse.schema import (
    PacBioRun,
    PacBioProductMetrics,
    PacBioRunWellMetrics,
    Study,
    Sample,
)
import pytest
from sqlalchemy.orm import Session

from lang_qc.db.qc_schema import (
    ProductLayout,
    QcState,
    QcStateDict,
    QcType,
    SeqPlatform,
    SeqProduct,
    SubProduct,
    SubProductAttr,
    User,
)


@pytest.fixture
def inbox_data(mlwhdb_test_sessionfactory):

    session: Session = mlwhdb_test_sessionfactory()

    timedeltas_labels = [(timedelta(days=i, minutes=2), f"A{i}") for i in range(9)]

    for delta, label in timedeltas_labels:

        metrics = PacBioRunWellMetrics(
            well_complete=datetime.now() - delta,
        )
        metrics.well_label = label
        metrics.pac_bio_run_name = "MARATHON"
        metrics.instrument_type = "pacbio"
        metrics.ccs_execution_mode = "None"
        metrics.well_status = "Complete"
        session.add(metrics)

        session.add(
            PacBioRun(
                well_label=label,
                pac_bio_run_name="MARATHON",
                last_updated=datetime.now(),
                recorded_at=datetime.now(),
                id_sample_tmp=0,
                id_study_tmp=0,
                id_pac_bio_run_lims=0,
                cost_code="hi",
                id_lims=1,
                plate_barcode="AAAAAAA",
                plate_uuid_lims="uuid",
                well_uuid_lims="uuid",
                pac_bio_library_tube_id_lims="id",
                pac_bio_library_tube_uuid="uuid",
                pac_bio_library_tube_name="bob",
                pac_bio_product_metrics=[
                    PacBioProductMetrics(pac_bio_run_well_metrics=metrics)
                ],
                study=Study(
                    id_lims="id",
                    id_study_lims=f"linny{label}",
                    last_updated=datetime.now(),
                    recorded_at=datetime.now(),
                ),
                sample=Sample(
                    id_lims="id",
                    id_sample_lims=f"linny{label}",
                    last_updated=datetime.now(),
                    recorded_at=datetime.now(),
                ),
            )
        )

    session.commit()


@pytest.fixture
def filtered_inbox_data(qcdb_test_sessionfactory, inbox_data):

    qc_session: Session = qcdb_test_sessionfactory()

    passed = QcStateDict(
        state="Passed",
        outcome=1,
    )
    failed = QcStateDict(
        state="Failed",
        outcome=2,
    )
    claimed = QcStateDict(
        state="Claimed",
        outcome=6,
    )
    on_hold = QcStateDict(state="On hold", outcome=7)

    library_type = QcType(qc_type="library", description="Sample/library evaluation")

    pacbio_platform = SeqPlatform(name="PacBio", description="Pacific Biosciences")

    well_label_attr = SubProductAttr(
        attr_name="well_label", description="PacBio well (or cell) label"
    )

    run_name_attr = SubProductAttr(
        attr_name="run_name", description="The name of the PacBio run according to LIMS"
    )

    test_user = User(username="test_user")

    qc_session.add_all(
        [
            passed,
            failed,
            claimed,
            on_hold,
            library_type,
            pacbio_platform,
            run_name_attr,
            well_label_attr,
            test_user,
        ]
    )
    qc_session.commit()

    qc_session.add(
        QcState(
            created_by="test_framework",
            is_preliminary=False,
            date_created=datetime.now(),
            date_updated=datetime.now(),
            qc_state_dict=passed,
            qc_type=library_type,
            seq_product=SeqProduct(
                id_product="TESTPRODUCT",
                seq_platform=pacbio_platform,
                product_layout=[
                    ProductLayout(
                        sub_product=SubProduct(
                            id_attr_one=run_name_attr.id_attr,
                            id_attr_two=well_label_attr.id_attr,
                            value_attr_one="MARATHON",
                            value_attr_two="A2",
                            properties={},
                            properties_digest="chatperche",
                        )
                    )
                ],
            ),
            user=test_user,
        )
    )
    qc_session.commit()
