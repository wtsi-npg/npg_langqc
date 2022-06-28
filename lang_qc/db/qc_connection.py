# Copyright (c) 2022 Genome Research Ltd.
#
# Author: Adam Blanchet <ab59@sanger.ac.uk>
#
# This file is part of npg_langqc.
#
# npg_langqc is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

config = {"QCDB_URL": os.environ.get("QCDB_URL"), "TEST": os.environ.get("LANGQC_MODE")}

if config["TEST"]:
    config["QCDB_URL"] = "sqlite+pysqlite:///:memory:"

if config["QCDB_URL"] is None or config["QCDB_URL"] == "":
    raise Exception(
        "ENV['QCDB_URL'] must be set with a database URL, or LANGQC_MODE must be set for testing."
    )

engine = create_engine(config["QCDB_URL"], future=True, echo=True)
session_factory: sessionmaker = sessionmaker(engine, expire_on_commit=False)


def get_qc_db() -> Session:
    """Get QC DB connection"""
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
