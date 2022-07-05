import configparser
import os

import pytest
from fastapi.testclient import TestClient
from ml_warehouse.schema import Base as MlwhBase
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from lang_qc.main import app
from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import Base as QcBase

test_ini = os.path.join(os.path.dirname(__file__), "testdb.ini")


@pytest.fixture(scope="session")
def config() -> configparser.ConfigParser:
    # Database credentials for the test MySQL instance are stored here. This
    # should be an instance in a container, discarded after each test run.
    test_config = configparser.ConfigParser()
    test_config.read(test_ini)
    return test_config


def mysql_url(
    config: configparser.ConfigParser,
    section: str,
    default_user: str,
    default_password: str,
    default_ip: str,
    default_port: str,
    default_schema: str,
):
    """Returns a MySQL URL configured through an ini file.

    The keys and values are:

    [<section>]
    user = <database user, defaults to default_user>
    password = <database password, defaults to default_password>
    ip_address = <database IP address, defaults to default_ip>
    port = <database port, defaults to default_port>
    schema = <database schema, defaults to default_schema>
    """

    if section not in config.sections():
        raise configparser.Error(
            f"The {section} configuration section is missing. "
            "You need to fill this in before running "
            f"tests on a {section} database"
        )

    connection_conf = config[section]
    user = connection_conf.get("user", default_user)
    password = connection_conf.get("password", default_password)
    ip_address = connection_conf.get("ip_address", default_ip)
    port = connection_conf.get("port", default_port)
    schema = connection_conf.get("schema", default_schema)

    return (
        f"mysql+pymysql://{user}:{password}@"
        f"{ip_address}:{port}/{schema}?charset=utf8mb4"
    )


@pytest.fixture(scope="function", name="mlwhdb_test_sessionfactory")
def create_mlwhdb_test_sessionfactory(config):
    """Create a MLWH SQLAlchemy session factory, using credentials from config.

    If the config is missing certain values, they will default to:
        - user: test
        - password: test
        - host: 127.0.0.1
        - port: 3307
        - schema_name: mlwarehouse
    """

    url = mysql_url(
        config, "MySQL MLWH", "test", "test", "127.0.0.1", "3306", "mlwarehouse"
    )
    engine = create_engine(url, future=True)
    TestingSessionLocal = sessionmaker(bind=engine)

    with engine.connect() as conn:
        # Workaround for invalid default values for dates.
        conn.execute(text("SET sql_mode = '';"))
        conn.commit()
        # Make it easier to populate the tables
        conn.execute(text("SET foreign_key_checks=0;"))
        conn.commit()
    # Drop all tables and then create them to make it easier to test locally too.
    MlwhBase.metadata.drop_all(bind=engine)
    MlwhBase.metadata.create_all(bind=engine)

    return TestingSessionLocal


@pytest.fixture(scope="function", name="qcdb_test_sessionfactory")
def create_qcdb_test_sessionfactory(config):
    """Create a QC DB SQLAlchemy session factory, using credentials from config.

    If the config is missing certain valuse, they will default to:
        - user: test
        - password: test
        - host: 127.0.0.1
        - port: 3307
        - schema_name: langqc
    """

    url = mysql_url(config, "MySQL QCDB", "test", "test", "127.0.0.1", "3307", "langqc")
    engine = create_engine(url, future=True)
    TestingSessionLocal = sessionmaker(bind=engine)

    # Drop all tables and then create then to make it easier to test locally too.
    QcBase.metadata.drop_all(bind=engine)
    QcBase.metadata.create_all(bind=engine)

    return TestingSessionLocal


@pytest.fixture(scope="function", name="test_client")
def create_test_client(
    config, mlwhdb_test_sessionfactory, qcdb_test_sessionfactory
) -> TestClient:
    def override_get_mlwh_db():
        try:
            db: Session = mlwhdb_test_sessionfactory()
            yield db
        finally:
            db.close()

    def override_get_qc_db():
        try:
            db: Session = qcdb_test_sessionfactory()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_mlwh_db] = override_get_mlwh_db
    app.dependency_overrides[get_qc_db] = override_get_qc_db
    client = TestClient(app)

    return client
