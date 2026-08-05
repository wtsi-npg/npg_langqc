import configparser
import importlib
import os
import os.path
import pathlib
import re

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert, text
from sqlalchemy.orm import Session, sessionmaker

from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.mlwh_schema import Base as MlwhBase
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import Base as QcBase
from lang_qc.main import app

test_ini = os.path.join(os.path.dirname(__file__), "testdb.ini")


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


def insert_from_yaml(session, dir_path, module_name):
    # Load the schema module where the table ORM classes are defined.
    module = importlib.import_module(module_name)

    # Find all files in a given directory.
    dir_obj = pathlib.Path(dir_path)
    file_paths = list(str(f) for f in dir_obj.iterdir())
    file_paths.sort()

    for file_path in file_paths:
        with open(file_path, "r") as f:
            (head, file_name) = os.path.split(file_path)
            # File name example: 200-PacBioRun.yml
            m = re.match(r"\A\d+-([a-zA-Z]+)\.yml\Z", file_name)
            if m is not None:
                class_name = m.group(1)
                table_class = getattr(module, class_name)
                data = yaml.safe_load(f)
                session.execute(insert(table_class), data)

    session.commit()


def compare_dates(date_obj, date_string):
    assert date_obj.isoformat(sep=" ", timespec="seconds") == date_string


@pytest.fixture(scope="package")
def config() -> configparser.ConfigParser:
    # Database credentials for the test MySQL instance are stored here. This
    # should be an instance in a container, discarded after each test run.
    test_config = configparser.ConfigParser()
    test_config.read(test_ini)
    return test_config


@pytest.fixture(scope="module", name="mlwhdb_test_sessionfactory")
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
    engine = create_engine(url)
    TestingSessionLocal = sessionmaker(bind=engine)
    with engine.connect() as conn:
        # Workaround for invalid default values for dates.
        # Needed only in CI.
        conn.execute(text("SET sql_mode = '';"))
        conn.commit()
    # Drop all tables and then create them to make it easier to test locally too.
    MlwhBase.metadata.drop_all(bind=engine)
    MlwhBase.metadata.create_all(bind=engine)

    return TestingSessionLocal


@pytest.fixture(scope="module", name="mlwhdb_test_session")
def mlwhdb_test_session(mlwhdb_test_sessionfactory):
    with mlwhdb_test_sessionfactory() as session:
        yield session


@pytest.fixture(scope="module", name="qcdb_test_sessionfactory")
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
    engine = create_engine(url)
    TestingSessionLocal = sessionmaker(bind=engine)
    with engine.connect() as conn:
        # Workaround for invalid default values for dates.
        conn.execute(text("SET sql_mode = '';"))
        conn.commit()
        # Make it easier to populate the tables
        conn.execute(text("SET foreign_key_checks=0;"))
        conn.commit()
    # Drop all tables and then create then to make it easier to test locally too.
    QcBase.metadata.drop_all(bind=engine)
    QcBase.metadata.create_all(bind=engine)

    return TestingSessionLocal


@pytest.fixture(scope="module", name="qcdb_test_session")
def qcdb_test_session(qcdb_test_sessionfactory):
    with qcdb_test_sessionfactory() as session:
        yield session


@pytest.fixture(scope="module", name="test_client")
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


@pytest.fixture(scope="module", name="mlwhdb_load_runs")
def mlwhdb_load_from_yaml(mlwhdb_test_session):
    insert_from_yaml(
        mlwhdb_test_session, "tests/data/mlwh_pb_runs", "lang_qc.db.mlwh_schema"
    )
