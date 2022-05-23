import configparser
import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from ml_warehouse.schema import (
    Base,
    PacBioRun,
    PacBioRunWellMetrics,
    PacBioProductMetrics,
    Study,
    Sample,
)
from lang_qc.main import app
from lang_qc.db.mlwh_connection import get_mlwh_db

test_ini = os.path.join(os.path.dirname(__file__), "testdb.ini")


@pytest.fixture(scope="session")
def config() -> configparser.ConfigParser:
    # Database credentials for the test MySQL instance are stored here. This
    # should be an instance in a container, discarded after each test run.
    test_config = configparser.ConfigParser()
    test_config.read(test_ini)
    yield test_config


def mysql_url(config: configparser.ConfigParser):
    """Returns a MySQL URL configured through an ini file.

    The keys and values are:

    [MySQL]
    user       = <database user, defaults to "mlwh">
    password   = <database password, defaults to empty i.e. "">
    ip_address = <database IP address, defaults to "127.0.0.1">
    port       = <database port, defaults to 3306>
    schema     = <database schema, defaults to "mlwh">
    """
    section = "MySQL"

    if section not in config.sections():
        raise configparser.Error(
            "The {} configuration section is missing. "
            "You need to fill this in before running "
            "tests on a {} database".format(section, section)
        )
    connection_conf = config[section]
    user = connection_conf.get("user", "mlwh")
    password = connection_conf.get("password", "")
    ip_address = connection_conf.get("ip_address", "127.0.0.1")
    port = connection_conf.get("port", "3306")
    schema = connection_conf.get("schema", "mlwh")

    return (
        f"mysql+pymysql://{user}:{password}@"
        f"{ip_address}:{port}/{schema}?charset=utf8mb4"
    )


def create_test_data(session: Session):

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


@pytest.fixture(scope="session")
def client(config) -> TestClient:
    engine = create_engine(mysql_url(config), future=True)

    TestingSessionLocal = sessionmaker(bind=engine)
    print(engine.url)
    with engine.connect() as conn:
        # Workaround for invalid default values for dates.
        conn.execute(text("SET sql_mode = '';"))
        conn.commit()
        # Make it easier to populate the tables
        conn.execute(text("SET foreign_key_checks=0;"))
        conn.commit()
    # Drop all tables and then create them to make it easier to test locally too.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    create_test_data(TestingSessionLocal())

    def override_get_mlwh_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_mlwh_db] = override_get_mlwh_db

    client = TestClient(app)

    yield client
