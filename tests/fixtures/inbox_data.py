from datetime import datetime, timedelta

import pytest
from npg_id_generation.pac_bio import PacBioEntity

from lang_qc.db.mlwh_schema import (
    PacBioProductMetrics,
    PacBioRun,
    PacBioRunWellMetrics,
    Sample,
    Study,
)
from lang_qc.db.qc_schema import (
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
def inbox_data(mlwhdb_test_session):

    timedeltas_labels = [(timedelta(days=i, minutes=2), f"A{i}") for i in range(9)]

    for delta, label in timedeltas_labels:

        metrics = PacBioRunWellMetrics(
            well_complete=datetime.now() - delta,
            run_complete=datetime.now() - delta,
        )
        metrics.well_label = label
        metrics.pac_bio_run_name = "MARATHON"
        metrics.instrument_type = "pacbio"
        metrics.ccs_execution_mode = "None"
        metrics.well_status = "Complete"
        metrics.id_pac_bio_product = PacBioEntity(run_name="MARATHON", well_label=label)
        if label == "A1":
            # Fill in QC data
            metrics.productive_zmws_num = 8007271
            metrics.binding_kit = "Sequel II Binding Kit 2.2"
            metrics.control_num_reads = 7400
            metrics.control_read_length_mean = 51266
            metrics.hifi_read_bases = 28534670263
            metrics.hifi_read_length_mean = 11619
            metrics.local_base_rate = 2.7341
            metrics.p0_num = 2602438
            metrics.p1_num = 5288229
            metrics.p2_num = 124004
            metrics.polymerase_read_bases = 534419894800
            metrics.polymerase_read_length_mean = 101200
            metrics.movie_minutes = 1800
            metrics.sl_run_uuid = "05b0a368-2548-11ed-861d-0242ac120002"
            metrics.sl_hostname = "esa_host"
        mlwhdb_test_session.add(metrics)

        mlwhdb_test_session.add(
            PacBioRun(
                well_label=label,
                pac_bio_run_name="MARATHON",
                last_updated=datetime.now(),
                recorded_at=datetime.now(),
                pipeline_id_lims="pipeline type 1",
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

    mlwhdb_test_session.commit()

    yield True
