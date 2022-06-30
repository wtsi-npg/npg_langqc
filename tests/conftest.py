import configparser
import os

import pytest
from fastapi.testclient import TestClient
from ml_warehouse.schema import Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from lang_qc.main import app
from lang_qc.db.mlwh_connection import get_mlwh_db

test_ini = os.path.join(os.path.dirname(__file__), "testdb.ini")


@pytest.fixture(scope="session")
def config() -> configparser.ConfigParser:
    # Database credentials for the test MySQL instance are stored here. This
    # should be an instance in a container, discarded after each test run.
    test_config = configparser.ConfigParser()
    test_config.read(test_ini)
    return test_config


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


@pytest.fixture(scope="function", name="mlwhdb_test_sessionfactory")
def create_mlwhdb_test_sessionfactory(config):
    engine = create_engine(mysql_url(config), future=True)

    TestingSessionLocal = sessionmaker(bind=engine)

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

    return TestingSessionLocal


@pytest.fixture(scope="function", name="test_client")
def create_test_client(config, mlwhdb_test_sessionfactory) -> TestClient:
    def override_get_mlwh_db():
        try:
            db: Session = mlwhdb_test_sessionfactory()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_mlwh_db] = override_get_mlwh_db

    client = TestClient(app)

    return client
