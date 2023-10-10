# Copyright (c) 2022, 2023 Genome Research Ltd.
#
# Authors:
#  Adam Blanchet
#  Marina Gourtovaia <mg8@sanger.ac.uk>
#  Kieron Taylor <kt19@sanger.ac.uk>
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

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from lang_qc.db.qc_schema import QcState as QcStateDB


class QcStateBasic(BaseModel):
    """
    Represents basic QC data associated with a QC-able entity.
    """

    qc_state: str = Field(
        default=None,
        title="QC state",
        description="""
        The QC state of the type defined by the `qc_type` attribute.
        """,
    )
    is_preliminary: bool = Field(default=None, title="Preliminary state of the outcome")
    qc_type: str = Field(default=None, title="Type of QC performed")


class QcState(QcStateBasic):
    """
    Represents QC data associated with a QC-able entity.

    The definition of the inherited `qc_state` attribute of this class should
    read as follows:
        'For an entity defined by the `id_seq_product` attribute value, the
        assigned QC state of the type defined by the `qc_type` attribute'.
    """

    outcome: Optional[bool] = Field(
        default=None,
        title="Boolean QC outcome",
        description="""
        A boolean QC outcome corresponding to the value of the `state` attribute.
        A False value corresponds to a QC fail, a True value corresponds to a QC
        pass, an undefined value means that the QC state is neither a pass nor
        a fail (example - 'on hold').
        """,
    )
    id_product: str = Field(default=None, title="Unique entity ID")
    date_created: datetime = Field(
        default=None,
        title="Date the initial state was assigned",
        description="""
        Each entity can have a number of QC states associated with it. This date
        corresponds to the date the initial QC state was assigned.
        """,
    )
    date_updated: datetime = Field(
        default=None,
        title="Date the state was updated",
        description="""
        This date corresponds to the date when the QC state defined by the `state`
        attribute of this object was assigned.
        """,
    )
    user: str = Field(default=None, title="User who assigned current QC state")
    created_by: str = Field(
        default=None,
        title="This QC state assignment context",
        description="""
        QC state assignment context, i.e. the name of the web application,
        script name, JIRA ticket number, etc., which is associated with the
        assignment of the this QC state.
        """,
    )
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: QcStateDB):
        """
        A class factory method. Given a database object representing the
        QC state, returns an instance of this class object.
        """

        return cls(
            user=obj.user.username,
            date_created=obj.date_created,
            date_updated=obj.date_updated,
            qc_type=obj.qc_type.qc_type,
            qc_state=obj.qc_state_dict.state,
            outcome=obj.qc_state_dict.outcome
            if obj.qc_state_dict.outcome is not None
            else None,
            is_preliminary=bool(obj.is_preliminary),
            created_by=obj.created_by,
            id_product=obj.seq_product.id_product,
        )
