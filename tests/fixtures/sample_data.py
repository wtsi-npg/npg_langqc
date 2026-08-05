from datetime import datetime

import pytest
from npg_id_generation.pac_bio import PacBioEntity

from lang_qc.db.mlwh_schema import (
    PacBioProductMetrics,
    PacBioRun,
    PacBioRunWellMetrics,
    Sample,
    Study,
)


@pytest.fixture(scope="function", params=["AAAAAAAA", None])
def simplex_run(request, mlwhdb_test_session):
    """
    A single sample, well, run mlwh fixture that provides both an explicit tag1
    for the sample, and an implicit default tag (when the PacBio instrument is
    run with default barcodes)
    """
    run_name = "RUN-9999"
    run_name += request.param if request.param else ""
    well_label = "A1"
    plate_number = 1
    tag1 = request.param
    now = datetime.now()

    common_run_attribs = {
        "recorded_at": now,
        "last_updated": now,
        "pipeline_id_lims": "nobody cares",
        "cost_code": "probably ToL",
        "id_lims": 1,
        "plate_uuid_lims": "uuid1",
        "well_uuid_lims": "uuid1",
        "pac_bio_library_tube_id_lims": "id",
        "pac_bio_library_tube_uuid": "uuid",
        "pac_bio_library_tube_name": "bob",
    }

    well_metrics_a1 = PacBioRunWellMetrics(
        pac_bio_run_name=run_name,
        well_label=well_label,
        plate_number=plate_number,
        instrument_type="Revio",
        id_pac_bio_product=PacBioEntity(
            run_name=run_name,
            well_label=well_label,
            plate_number=plate_number,
        ).hash_product_id(),
        demultiplex_mode=None,
    )

    product = PacBioProductMetrics(
        id_pac_bio_product=PacBioEntity(
            run_name=run_name,
            well_label=well_label,
            plate_number=plate_number,
            tags=tag1,
        ).hash_product_id(),
        qc=1,
        hifi_read_bases=90000000,
        hifi_num_reads=10,
        hifi_read_length_mean=9000000,
        barcode_quality_score_mean=34,
        hifi_bases_percent=90.001,
        pac_bio_run_well_metrics=well_metrics_a1,
        barcode4deplexing=None,
    )

    study = Study(
        id_lims="id",
        id_study_lims="1",
        recorded_at=now,
        last_updated=now,
    )

    # This run-well-plate has one singly tagged sample
    id_sample_lims = request.param or "1"
    simplex_run = PacBioRun(
        pac_bio_run_name=run_name,
        well_label=well_label,
        plate_number=plate_number,
        id_pac_bio_run_lims=0,
        sample=Sample(
            id_lims="id",
            id_sample_lims=id_sample_lims,
            uuid_sample_lims=f"uuid_{id_sample_lims}",
            recorded_at=now,
            last_updated=now,
        ),
        study=study,
        plate_barcode="ABCD",
        pac_bio_product_metrics=[product],
        **common_run_attribs,
    )
    mlwhdb_test_session.add(simplex_run)
    mlwhdb_test_session.commit()
    yield simplex_run
    mlwhdb_test_session.delete(simplex_run)
    mlwhdb_test_session.delete(study)
    mlwhdb_test_session.delete(product)
    mlwhdb_test_session.delete(well_metrics_a1)
    mlwhdb_test_session.commit()


@pytest.fixture(scope="function")
def multiplexed_run(mlwhdb_test_session):
    "runs for several (2) samples in one run-well-plate"

    run_name = "RUN"
    well_label = "B1"
    plate_number = 1
    now = datetime.now()

    common_run_attribs = {
        "recorded_at": now,
        "last_updated": now,
        "pipeline_id_lims": "nobody cares",
        "cost_code": "probably ToL",
        "id_lims": 1,
        "plate_uuid_lims": "uuid1",
        "well_uuid_lims": "uuid1",
        "pac_bio_library_tube_id_lims": "id",
        "pac_bio_library_tube_uuid": "uuid",
        "pac_bio_library_tube_name": "bob",
    }

    study = Study(
        id_lims="id",
        id_study_lims="1",
        recorded_at=now,
        last_updated=now,
    )

    tag1 = "TTTTTTTT"
    tag1_2 = "GGGGGGGG"
    well_metrics_b1 = PacBioRunWellMetrics(
        pac_bio_run_name=run_name,
        well_label=well_label,
        plate_number=plate_number,
        instrument_type="Revio",
        id_pac_bio_product=PacBioEntity(
            run_name=run_name,
            well_label=well_label,
            plate_number=plate_number,
        ).hash_product_id(),
        hifi_num_reads=30,
        demultiplex_mode="OnInstrument",
    )

    product_1 = PacBioProductMetrics(
        id_pac_bio_product=PacBioEntity(
            run_name=run_name,
            well_label=well_label,
            plate_number=plate_number,
            tags=tag1,
        ).hash_product_id(),
        qc=1,
        hifi_read_bases=90000000,
        hifi_num_reads=20,
        hifi_read_length_mean=4500000,
        barcode_quality_score_mean=34,
        hifi_bases_percent=90.001,
        pac_bio_run_well_metrics=well_metrics_b1,
        barcode4deplexing="bc10--bc10",
    )

    multiplex_run_1 = PacBioRun(
        pac_bio_run_name=run_name,
        well_label=well_label,
        plate_number=plate_number,
        id_pac_bio_run_lims=1,
        sample=Sample(
            id_lims="pooled_id_1",
            id_sample_lims="2",
            uuid_sample_lims="uuid_2",
            name="It's a test",
            recorded_at=now,
            last_updated=now,
        ),
        study=study,
        plate_barcode="ABCD",
        pac_bio_product_metrics=[product_1],
        **common_run_attribs,
    )

    product_2 = PacBioProductMetrics(
        id_pac_bio_product=PacBioEntity(
            run_name=run_name,
            well_label=well_label,
            plate_number=plate_number,
            tags=tag1_2,
        ).hash_product_id(),
        qc=1,
        hifi_read_bases=10000000,
        hifi_num_reads=10,
        hifi_read_length_mean=1000000,
        barcode_quality_score_mean=34,
        hifi_bases_percent=100.00,
        pac_bio_run_well_metrics=well_metrics_b1,
        barcode4deplexing="bc11--bc11",
    )

    multiplex_run_2 = PacBioRun(
        pac_bio_run_name=run_name,
        well_label=well_label,
        plate_number=plate_number,
        id_pac_bio_run_lims=2,
        sample=Sample(
            id_lims="pooled_id_2",
            id_sample_lims="3",
            uuid_sample_lims="uuid_3",
            recorded_at=now,
            last_updated=now,
        ),
        study=study,
        plate_barcode="ABCD",
        pac_bio_product_metrics=[product_2],
        **common_run_attribs,
    )

    mlwhdb_test_session.add_all([multiplex_run_1, multiplex_run_2])
    mlwhdb_test_session.commit()
    yield (multiplex_run_1, multiplex_run_2)
    mlwhdb_test_session.delete(multiplex_run_1)
    mlwhdb_test_session.delete(multiplex_run_2)
    mlwhdb_test_session.delete(study)
    mlwhdb_test_session.delete(well_metrics_b1)
    mlwhdb_test_session.delete(product_1)
    mlwhdb_test_session.delete(product_2)
    mlwhdb_test_session.commit()


# Some runs use "default barcodes" and the tag1 fields in pac_bio_run are empty. When this is true, we also lose the deplex stats
# Show user "default" in the interface?
# Not all runs get any hifi stats in pac_bio_product_metrics. Not all runs use the hifi reads setting
