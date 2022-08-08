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

engine = None
session_factory = None


def get_qc_db() -> Session:
    """Get QC DB connection"""

    global engine, session_factory

    if engine is None:
        url = os.environ.get("QCDB_URL")
        if url is None or url == "":
            raise Exception("ENV['QCDB_URL'] must be set with a database URL")
        engine = create_engine(url, future=True)

    if session_factory is None:
        session_factory = sessionmaker(engine)

    db = session_factory()
    try:
        yield db
    finally:
        db.close()
