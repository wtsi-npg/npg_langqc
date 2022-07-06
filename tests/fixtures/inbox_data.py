from datetime import datetime, timedelta
from typing import List, Tuple

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
    # Don't forget to close the session.
    session.close()


@pytest.fixture()
def filtered_inbox_data(mlwhdb_test_sessionfactory, qcdb_test_sessionfactory):

    qc_db_session: Session = qcdb_test_sessionfactory()
    mlwh_db_session: Session = mlwhdb_test_sessionfactory()

    desired_wells = {
        "MARATHON": {"A1": "Passed", "A2": "Passed", "A3": "On hold", "A4": None},
        "SEMI-MARATHON": {"A1": "Failed", "A2": "Claimed", "A3": "Claimed", "A4": None},
        "QUARTER-MILE": {"A1": None, "A2": "On hold", "A3": "On hold", "A4": None},
    }

    # Setup dicts and "filler" data
    library_qc_type = QcType(qc_type="Library", description="Library QC")

    run_name_attr = SubProductAttr(attr_name="run_name", description="PacBio run name.")
    well_label_attr = SubProductAttr(
        attr_name="well_label", description="PacBio well label"
    )
    seq_platform = SeqPlatform(name="PacBio", description="Pacific Biosciences.")
    user = User(username="zx80")
    states = ["Passed", "Failed", "Claimed", "On hold"]
    state_dicts = {}

    for state in states:
        state_dicts[state] = QcStateDict(state=state, outcome=states.index(state))

    qc_db_session.add_all(state_dicts.values())
    qc_db_session.add_all(
        [library_qc_type, run_name_attr, well_label_attr, seq_platform, user]
    )
    qc_db_session.commit()

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
        qc_db_session.add(state)
    qc_db_session.commit()

    for well in run_metrics:
        mlwh_db_session.add(well)
    mlwh_db_session.commit()

    # Don't forget to close the sessions
    qc_db_session.close()
    mlwh_db_session.close()

    return desired_wells


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
