# Copyright (c) 2022 Genome Research Ltd.
#
# Author: Marina Gourtovaia <mg8@sanger.ac.uk>
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
# this program. If not, see <http://www.gnu.org/licenses/>

"""
A module bringing together classes used in QC state assignments for a PacBio
well. A low-level API for the assignment of QC states, which does not depend on
the web framework.
"""

from datetime import datetime
from functools import cached_property
from typing import Dict

from ml_warehouse.schema import PacBioRunWellMetrics
from npg_id_generation.pac_bio import PacBioEntity
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from lang_qc.db.qc_schema import (
    ProductLayout,
    QcState,
    QcStateDict,
    QcStateHist,
    QcType,
    SeqPlatform,
    SeqProduct,
    SubProduct,
    SubProductAttr,
    User,
)

APPLICATION_NAME = "LangQC"
DEFAULT_QC_TYPE = "sequencing"
DEFAULT_QC_STATE = "Claimed"
DEFAULT_FINALITY = False
ONLY_PRELIM_STATES = (DEFAULT_QC_STATE, "On hold")


class InvalidDictValueError(Exception):
    """
    Custom exception for failures to validate input that should
    correspond to database dictionaries values such as, for example,
    and unknown QC type.
    """


class InconsistentInputError(Exception):
    """
    Custom exception for cases when individual values of attributes
    are valid, but are inconsistent or mutually exclusive in regards
    of the QC state that has to be assigned.
    """


class WellMetrics(BaseModel):
    """
    A data access class for routine SQLAlchemy operations on well data
    in ml warehouse database.
    """

    session: Session = Field(
        title="SQLAlchemy Session",
        description="A SQLAlchemy Session for the ml warehouse database",
    )
    run_name: str = Field(title="Name of the run as known in LIMS")
    well_label: str = Field(title="Well label as known in LIMS and SMRT Link")

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True

    def get_metrics(self) -> PacBioRunWellMetrics | None:
        """
        Returns a well row record from the well metrics table or
        None if the record does not exist.
        """

        return self.session.execute(
            select(PacBioRunWellMetrics).where(
                and_(
                    PacBioRunWellMetrics.pac_bio_run_name == self.run_name,
                    PacBioRunWellMetrics.well_label == self.well_label,
                )
            )
        ).scalar_one_or_none()

    def exists(self) -> bool:
        """
        Returns `True` if a record for combination of a well and a run exists,
        in the well metrics table `False` otherwise.
        """

        return bool(self.get_metrics())


class QcDictDB(BaseModel):
    """
    A cache layer for LangQC database dictionary entries.
    """

    session: Session = Field(
        title="SQLAlchemy Session",
        description="A SQLAlchemy Session for the LangQC database",
    )

    class Config:
        arbitrary_types_allowed = True
        # A workaround for a bug in pydantic in order to use the cached_property
        # decorator.
        keep_untouched = (cached_property,)

    @cached_property
    def qc_types(self) -> Dict:
        """
        A cached dictionary of QC type dictionary rows, where the QcType objects
        representing the database rows are values and the string descriptions of the
        QC types are keys.
        """

        db_types = self.session.execute(select(QcType)).scalars().all()
        return {row.qc_type: row for row in db_types}

    def qc_type_dict_row(self, qc_type_name: str) -> QcType:
        """
        Given a description of the QC type, returns an object that
        corresponds to a relevant row in the `qc_type` table.
        Raises a `ValidationError` if no corresponding record is found.
        """

        if qc_type_name not in self.qc_types.keys():
            raise InvalidDictValueError(f"QC type '{qc_type_name}' is invalid")

        return self.qc_types[qc_type_name]

    @cached_property
    def qc_states(self) -> Dict:
        """
        A cached dictionary of QC state dictionary rows, where the QcStateDict objects
        representing the database rows are values abd the string descriptions of the
        state are keys.
        """

        db_states = (
            self.session.execute(
                select(QcStateDict).order_by(
                    QcStateDict.outcome.desc(), QcStateDict.state
                )
            )
            .scalars()
            .all()
        )

        return {row.state: row for row in db_states}

    def qc_state_dict_row(self, qc_state_name: str) -> QcStateDict:
        """
        Given a description of the QC state, returns an object that
        corresponds to a relevant row in the `qc_state_dict` table.
        Raises a `ValidationError` if no corresponding dictionary record
        is found.
        """

        if qc_state_name not in self.qc_states.keys():
            raise InvalidDictValueError(f"QC state '{qc_state_name}' is invalid")

        return self.qc_states[qc_state_name]


class WellQc(QcDictDB):
    """
    A data access class for routine SQLAlchemy operations on PacBio well
    QC data in LangQC database.
    """

    run_name: str = Field(title="Name of the run as known in LIMS")
    well_label: str = Field(title="Well label as known in LIMS and SmrtLink")

    class Config:
        allow_mutation = False
        # A workaround for a bug in pydantic in order to use the cached_property
        # decorator.
        keep_untouched = (cached_property,)

    @cached_property
    def seq_product(self) -> SeqProduct:
        """
        Returns a pre-existing `lang_qc.db.qc_schema.SeqProduct`, or creates
        a new one. The property is computed lazily.
        """

        return self._find_or_create_well()

    @cached_property
    def product_definition(self) -> Dict:
        """
        A cached representation of the well as a dictionary with two keys,
        `id` - a unique product id and `json` - a json string representing
        this well, see `npg_id_generation.PacBioEntity` for details. This
        property is an outcome of a light-weight computation that does not
        involve querying the database. The property is computed lazily.
        """

        pbe = PacBioEntity(run_name=self.run_name, well_label=self.well_label)
        return {"id": pbe.hash_product_id(), "json": pbe.json()}

    def current_qc_state(self, qc_type: str = "sequencing") -> QcState | None:
        """
        Returns a current record for the product associated with this
        instance in the `qc_state` table for QC. The type of QC is defined
        by the `qc_type` argument.

        Validates the `qc_type` argument and raises a `ValidationError` if
        the validation fails.

        Returns `None` if no current QC record for this entity for this type
        of QC exists.
        """

        return (
            self.session.execute(
                select(QcState)
                .join(QcState.seq_product)
                .where(
                    and_(
                        SeqProduct.id_product == self.product_definition["id"],
                        QcState.qc_type == self.qc_type_dict_row(qc_type),
                    )
                )
            )
            .scalars()
            .one_or_none()
        )

    def assign_qc_state(
        self,
        user: User,
        qc_state: str = DEFAULT_QC_STATE,
        qc_type: str = DEFAULT_QC_TYPE,
        is_preliminary: bool = not DEFAULT_FINALITY,
        application: str = APPLICATION_NAME,
        date_updated: datetime = None,
    ) -> QcState:
        """
        Creates and persists a new QC state of type `qc_type` for this instance.
        Returns an QcState object representing the new/updated/unchanged
        row in the `qc_state` table.

        A new row is created if there was no corresponding QC state in the DB.

        The current row is returned if the current QC state in the DB matches
         `qc_type`, `qc_state` and `is_preliminary` arguments.

        An updated row is returned in all other cases.

        Changing of `qc_type` for an existing row is not permitted.

        Records for different types of QC for the same entity can co-exist.
        For example: A sequencing QC record
            (qc_type="sequencing", qc_state="DONE", is_preliminary=true)
        can exist at the same time as
            (qc_type="library", qc_state="DONE", is_preliminary=true)
        without conflict. These are independent kinds of QC assessment.

        A QC state change can be initiated by any user, and any QC state can
        replace any other. Enforcement of business rules must be handled at the
        application level.

        A `ValidationError` is raised if the values of either `qc_state` or `qc_type`
        attributes are invalid.

        For each new or updated record in the `qc_state` table a new record is
        created in the `qc_state_hist` table, thereby preserving a history of all
        changes.

        If a record for the product defined by this instance is not present in the
        `seq_product` table, it is created alongside corresponding records in the
        `sub_product` and `product_layout` tables.

        Arguments:

            user - an instance of the existing in the database lang_qc.db.qc_schema.User,
            object, required

            new_qc_state - a string description of the QC state to be assigned

            qc_type - a string representing QC type

            is_preliminary - a boolean value representing the preliminary nature of the
            QC state. False == final, i.e completed with no further changes intended.

            application - a string, the name of the application using this API,
            defaults to `Lang QC`. For differentiating between changes via GUI and
            other changes made by scripts or pipelines.

            date_updated - an optional `datetime` for explicitly setting when the QC state was
            changed. Normally the database will set the timestamp, but a manual setting can be
            used for testing and data manipulation. If the QC outcome for this entity does not
            exist, the value of this argument is used for the `date_created` column as well.
        """

        db_state = self.current_qc_state(qc_type)
        if (
            (db_state is not None)
            and (db_state.qc_state_dict.state == qc_state)
            and (bool(db_state.is_preliminary) == is_preliminary)
        ):
            # Do not update the state if it has not changed.
            # Return early, nothing more to do.
            return db_state

        qc_state_dict_row = self.qc_state_dict_row(qc_state)

        # 'Claimed' and 'On hold' states cannot be final.
        # By enforcing this we simplify rules for assigning QC states
        # to QC flow statuses.
        # Two options: either to change is_preliminary to True or error.
        if (is_preliminary is False) and (qc_state in ONLY_PRELIM_STATES):
            raise InconsistentInputError(f"QC state '{qc_state}' cannot be final")

        values = {
            "qc_state_dict": qc_state_dict_row,
            "is_preliminary": 1 if is_preliminary is True else 0,
            "user": user,
            "created_by": application,
            "qc_type": self.qc_types[qc_type],
            "seq_product": self.seq_product,
        }

        if db_state is not None:
            # Update some of the values of the existing record.
            # No need to update the QC type, it stays the same.
            db_state.qc_state_dict = values["qc_state_dict"]
            db_state.is_preliminary = values["is_preliminary"]
            db_state.user = values["user"]
            db_state.created_by = values["created_by"]
            if date_updated:
                db_state.date_updated = date_updated
        else:
            # Create a new record, date_updated=None is accepted by the ORM as
            # deferring to the schema defaults
            db_state = QcState(
                date_created=date_updated, date_updated=date_updated, **values
            )

        self.session.add(db_state)
        self.session.commit()  # to generate and propagate timestamps

        qc_state_hist = QcStateHist(
            # Clone timestamps whether from argument or generated by the DB
            date_created=db_state.date_created,
            date_updated=db_state.date_updated,
            **values,
        )

        self.session.add(qc_state_hist)
        self.session.commit()

        return db_state

    def _find_or_create_well(self) -> SeqProduct:

        well_product = (
            self.session.execute(
                select(SeqProduct).where(
                    SeqProduct.id_product == self.product_definition["id"]
                )
            )
            .scalars()
            .one_or_none()
        )

        if well_product is None:
            well_product = self._create_well()

        return well_product

    def _create_well(self) -> SeqProduct:

        id_seq_platform = (
            self.session.execute(
                select(SeqPlatform).where(SeqPlatform.name == "PacBio")
            )
            .scalar_one()
            .id_seq_platform
        )

        product_attr_id_rn = (
            self.session.execute(
                select(SubProductAttr).where(SubProductAttr.attr_name == "run_name")
            )
            .scalar_one()
            .id_attr
        )

        product_attr_id_wl = (
            self.session.execute(
                select(SubProductAttr).where(SubProductAttr.attr_name == "well_label")
            )
            .scalar_one()
            .id_attr
        )

        pd = self.product_definition
        product_id = pd["id"]
        product_json = pd["json"]
        # TODO: in future for composite products we have to check whether any of
        # the `sub_product` table entries we are linking to already exist.
        well_product = SeqProduct(
            id_product=product_id,
            id_seq_platform=id_seq_platform,
            product_layout=[
                ProductLayout(
                    sub_product=SubProduct(
                        id_attr_one=product_attr_id_rn,
                        value_attr_one=self.run_name,
                        id_attr_two=product_attr_id_wl,
                        value_attr_two=self.well_label,
                        properties=product_json,
                        properties_digest=product_id,
                    )
                )
            ],
        )

        self.session.add(well_product)
        self.session.commit()

        return well_product
