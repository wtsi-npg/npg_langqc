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
from tests.fixtures.utils import clean_mlwhdb, clean_qcdb


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

    clean_mlwhdb(mlwhdb_test_session)


@pytest.fixture()
def test_data_factory(mlwhdb_test_session, qcdb_test_session):
    def setup_data(desired_wells):
        # Setup dicts and "filler" data

        library_qc_type = QcType(
            qc_type="library", description="Sample/library evaluation"
        )
        seq_qc_type = QcType(
            qc_type="sequencing", description="Sequencing process evaluation"
        )

        run_name_attr = SubProductAttr(
            attr_name="run_name", description="PacBio run name."
        )
        well_label_attr = SubProductAttr(
            attr_name="well_label", description="PacBio well label"
        )
        seq_platform = SeqPlatform(name="PacBio", description="Pacific Biosciences.")
        user = User(username="zx80@example.com")
        other_user = User(username="cd32@example.com")
        states = ["Passed", "Failed", "Claimed", "On hold", "Aborted"]
        state_dicts = {}

        for state in states:
            outcome = None
            if state == "Passed":
                outcome = True
            elif state == "Failed":
                outcome = False
            state_dicts[state] = QcStateDict(state=state, outcome=outcome)

        qcdb_test_session.add_all(state_dicts.values())
        qcdb_test_session.add_all(
            [
                library_qc_type,
                seq_qc_type,
                run_name_attr,
                well_label_attr,
                seq_platform,
                user,
                other_user,
            ]
        )

        # Start adding the PacBioRunWellMetrics and QcState rows.
        for run_name, wells in desired_wells.items():
            for well_label, state in wells.items():

                pbe = PacBioEntity(run_name=run_name, well_label=well_label)
                id = pbe.hash_product_id()

                run_metrics = PacBioRunWellMetrics(
                    pac_bio_run_name=run_name,
                    well_label=well_label,
                    id_pac_bio_product=id,
                    instrument_type="PacBio",
                    polymerase_num_reads=1337,
                    ccs_execution_mode="None",
                    well_status="Complete",
                    run_start=datetime.now() - timedelta(days=3),
                    run_complete=datetime.now() - timedelta(days=1),
                    well_start=datetime.now() - timedelta(days=2),
                    well_complete=datetime.now() - timedelta(days=1),
                )
                mlwhdb_test_session.add(run_metrics)

                if state is not None:
                    json = pbe.model_dump_json()

                    qc_state = QcState(
                        created_by="me",
                        is_preliminary=state in ["On hold", "Claimed"],
                        qc_state_dict=state_dicts[state],
                        qc_type=seq_qc_type,
                        seq_product=SeqProduct(
                            id_product=id,
                            seq_platform=seq_platform,
                            sub_products=[
                                SubProduct(
                                    sub_product_attr=run_name_attr,
                                    sub_product_attr_=well_label_attr,
                                    value_attr_one=run_name,
                                    value_attr_two=well_label,
                                    properties=json,
                                    properties_digest=id,
                                ),
                            ],
                        ),
                        user=user,
                    )
                    qcdb_test_session.add(qc_state)
                    #  Feed back to fixture use
                    desired_wells[run_name][well_label] = qc_state

        qcdb_test_session.commit()
        mlwhdb_test_session.commit()

        return desired_wells

    yield setup_data

    clean_mlwhdb(mlwhdb_test_session)
    clean_qcdb(qcdb_test_session)
