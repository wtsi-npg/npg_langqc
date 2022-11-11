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
from npg_id_generation import PacBioEntity
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
DEFAULT_PRELIMINARILY = True
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


class WellQc(BaseModel):
    """
    A data access class for routine SQLAlchemy operations on well
    QC data in LangQC database.
    """

    session: Session = Field(
        title="SQLAlchemy Session",
        description="A SQLAlchemy Session for the LangQC database",
    )
    run_name: str = Field(title="Name of the run as known in LIMS")
    well_label: str = Field(title="Well label as known in LIMS and SmrtLink")

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True
        # A workaround for a bug in pydantic in order to use the cached_property
        # decorator.
        keep_untouched = (cached_property,)

    @cached_property
    def seq_product(self) -> SeqProduct:
        """
        A cached instance of the lang_qc.db.qc_schema.SeqProduct object.
        If the corresponding database record exists, this object corresponds
        to this pre-existing record. If at the time of accessing this property
        the record does not exist, it is created and returned. The property
        is computed lazily.
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

    def qc_state_dict_row(self, qc_state_description: str) -> QcStateDict:
        """
        Given a description of the QC state, returns an object that
        corresponds to a relevant row in the `qc_state_dict` table.
        Raises a `ValidationError` if no corresponding dictionary record
        is found.
        """

        valid = (
            self.session.execute(
                select(QcStateDict).where(QcStateDict.state == qc_state_description)
            )
            .scalars()
            .one_or_none()
        )

        if valid is None:
            raise InvalidDictValueError(f"QC state '{qc_state_description}' is invalid")

        return valid

    def qc_type_dict_row(self, qc_type_description: str) -> QcType:
        """
        Given a description of the QC type, returns an object that
        corresponds to a relevant row in the `qc_type` table.
        Raises a `ValidationError` if no corresponding record is found.
        """

        valid = (
            self.session.execute(
                select(QcType).where(QcType.qc_type == qc_type_description)
            )
            .scalars()
            .one_or_none()
        )

        if valid is None:
            raise InvalidDictValueError(f"QC type '{qc_type_description}' is invalid")

        return valid

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
        is_preliminary: bool = DEFAULT_PRELIMINARILY,
        application: str = APPLICATION_NAME,
        date_updated: datetime = datetime.utcnow(),
    ) -> QcState:
        """
        Tries to assign a new QC state for the QC type defined by the `qc_type`
        argument to the entity defined by this instance. Returns an object that
        corresponds to a new, updated or unchanged row in the `qc_state` table.

        A new row is returned if there was no corresponding QC assessment record.

        An unchanged existing row is returned if the current QC state for the
        requested qc type is the same as defined by the `qc_state` and `is_preliminary`
        arguments.

        An updated record is returned in all other cases.

        The method does not perform a conversion of one type of QC record into another.
        It allows for records for different types of QC for the same entity to co-exist.
        For example, if a sequencing QC record exists for the entity and the library QC
        record does not exist and the `qc_type` attribute of this method defines the
        library QC type, a new database record is created.

        The method does not enforce any particular order of assigning QC states,
        neither it mandates that all QC assignments for the entity should be
        performed by the same user.

        A `ValidationError` is raised if the values of either `qc_state` or `qc_type`
        attributes are invalid.

        For each new or updated record in the `qc_state` row table a new record is
        created in the `qc_state_hist` table.

        If a record for the product defined by this instance is not present in the
        `seq_product` table, it is created alongside corresponding records in the
        `sub_product` and `product_layout` tables.

        Arguments:

            user - an instance of the existing in the database lang_qc.db.qc_schema.User,
            object, required

            new_qc_state - a string description of the QC state to be assigned, defaults
            to `Claimed`

            qc_type - a string representing QC type, defaults to `sequencing`

            is_preliminary - a boolean value representing the preliminary nature of the
            QC state, defaults to `True`

            application - a string, the name of the application using this API,
            defaults to `Lang QC`

            date_updated - a `datetime`  object representing the time when the state
            was updated, defaults to UTC time for this moment in time; if this date
            is supplied by the caller, it is advised to adjust the value to the UTC
            time zone.

        """

        db_state = self.current_qc_state(qc_type)
        if (
            (db_state is not None)
            and (db_state.qc_state_dict.state == qc_state)
            and (db_state.qc_state.is_preliminary == is_preliminary)
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
            "is_preliminary": is_preliminary,
            "user": user,
            "created_by": application,
            "date_updated": date_updated,
        }

        if db_state is not None:
            # TODO: Any way not to hardcode column names?
            db_state.qc_state_dict = values["qc_state_dict"]
            db_state.is_preliminary = values["is_preliminary"]
            db_state.user = values["user"]
            db_state.created_by = values["created_by"]
            db_state.date_updated = values["date_updated"]
        else:
            # TODO: cache all qc types, this is a second call
            values["qc_type"] = self.qc_type_dict_row(qc_type)
            values["seq_product"] = self.seq_product
            values["date_created"] = date_updated
            db_state = QcState(**values)

        self.session.add_all([db_state, self._new_db_state_hist(db_state)])
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

    def _new_db_state_hist(self, db_qc_state: QcState) -> QcStateHist:

        data = {}
        for column_name in db_qc_state.__dict__:
            if (column_name.startswith("_") is False) and (
                column_name != "id_qc_state"
            ):
                data[column_name] = db_qc_state.__getattribute__(column_name)

        return QcStateHist(**data)
