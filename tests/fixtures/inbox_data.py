from datetime import datetime, timedelta
from typing import List, Tuple

import pytest
from ml_warehouse.schema import (
    PacBioProductMetrics,
    PacBioRun,
    PacBioRunWellMetrics,
    Sample,
    Study,
)
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
def inbox_data(mlwhdb_test_session):

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
        mlwhdb_test_session.add(metrics)

        mlwhdb_test_session.add(
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

    mlwhdb_test_session.commit()


@pytest.fixture()
def test_data_factory(mlwhdb_test_session, qcdb_test_session):
    def setup_data(desired_wells):
        # Setup dicts and "filler" data
        library_qc_type = QcType(
            qc_type="library", description="Sample/library evaluation"
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
        states = ["Passed", "Failed", "Claimed", "On hold"]
        state_dicts = {}

        for state in states:
            state_dicts[state] = QcStateDict(state=state, outcome=states.index(state))

        qcdb_test_session.add_all(state_dicts.values())
        qcdb_test_session.add_all(
            [
                library_qc_type,
                run_name_attr,
                well_label_attr,
                seq_platform,
                user,
                other_user,
            ]
        )
        qcdb_test_session.commit()

        # Start adding the PacBioRunWellMetrics and QcState rows.
        run_metrics = []
        states = []

        for run_name, wells in desired_wells.items():
            for well_label, state in wells.items():
                run_metrics.append(
                    PacBioRunWellMetrics(
                        pac_bio_run_name=run_name,
                        well_label=well_label,
                        instrument_type="PacBio",
                        polymerase_num_reads=1337,
                        ccs_execution_mode="None",
                        well_status="Complete",
                        well_complete=datetime.now() - timedelta(days=1),
                    )
                )
                if state is not None:
                    states.append(
                        QcState(
                            created_by="me",
                            is_preliminary=state in ["On hold", "Claimed"],
                            qc_state_dict=state_dicts[state],
                            qc_type=library_qc_type,
                            seq_product=SeqProduct(
                                id_product=run_name + well_label,
                                seq_platform=seq_platform,
                                product_layout=[
                                    ProductLayout(
                                        sub_product=SubProduct(
                                            sub_product_attr=run_name_attr,
                                            sub_product_attr_=well_label_attr,
                                            value_attr_one=run_name,
                                            value_attr_two=well_label,
                                            properties={run_name: well_label},
                                            properties_digest=run_name
                                            + well_label,  # dummy digest
                                        ),
                                    )
                                ],
                            ),
                            user=user,
                        )
                    )

        for state in states:
            qcdb_test_session.add(state)
        qcdb_test_session.commit()

        for well in run_metrics:
            mlwhdb_test_session.add(well)
        mlwhdb_test_session.commit()

        return desired_wells

    return setup_data


@pytest.fixture()
def wells_and_states() -> Tuple[List[PacBioRunWellMetrics], List[QcState]]:

    wells = {"MARATHON": ["A1", "A2", "A3", "A4"], "SEMI-MARATHON": ["A1", "A2", "A3"]}

    run_metrics = []
    states = []

    for run_name in wells:
        for well_label in wells[run_name]:
            run_metrics.append(
                PacBioRunWellMetrics(
                    pac_bio_run_name=run_name,
                    well_label=well_label,
                    instrument_type="PacBio",
                )
            )
            states.append(
                QcState(
                    id_qc_state_dict=1,
                    created_by="me",
                    seq_product=SeqProduct(
                        id_seq_platform="PacBio",
                        product_layout=[
                            ProductLayout(
                                sub_product=SubProduct(
                                    id_attr_one=1,
                                    value_attr_one=run_name,
                                    id_attr_two=2,
                                    value_attr_two=well_label,
                                )
                            )
                        ],
                    ),
                    user=User(username="zx80"),
                    qc_type=QcType(qc_type="library", description="library QC."),
                    qc_state_dict=QcStateDict(
                        state="Passed",
                        outcome=1,
                    ),
                )
            )

        return (run_metrics, states)
