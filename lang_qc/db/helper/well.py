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

from datetime import datetime
from functools import cached_property
from typing import Dict

from ml_warehouse.schema import PacBioRunWellMetrics
from npg_id_generation import PacBioEntity
from pydantic import BaseModel
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


class InvalidDictValueError(Exception):
    """
    Custom exception for failures to validate input that should
    correspond to database dictionaries values. Example: unknown
    QC type.
    """


class WellMetrics(BaseModel):

    """
    A data access class for routine sqlalchemy operations on well data
    in ml warehouse database.
    Instantiate with a sqlalchemy Session for the ml warehouse database.
    """

    session: Session
    run_name: str
    well_label: str

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
    A data access class for routine sqlalchemy operations on well
    QC data in lanqqc database.
    Instantiate with a sqlalchemy Session for the langqc database.
    """

    session: Session
    run_name: str
    well_label: str

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)

    @cached_property
    def seq_product(self) -> SeqProduct:

        return self._find_or_create_well()

    @cached_property
    def product_definition(self) -> Dict:

        pbe = PacBioEntity(run_name=self.run_name, well_label=self.well_label)
        return {"id": pbe.hash_product_id(), "json": pbe.json()}

    def valid_qc_state_dict(self, qc_state: str) -> QcStateDict:
        """
        Given a description of the QC state, returns an object that
        corresponds to a relevant row in the `qc_state_dict` table.
        Raises a `ValidationError` if no corresponding dictionary record
        is found.
        """

        valid = (
            self.session.execute(
                select(QcStateDict).where(QcStateDict.state == qc_state)
            )
            .scalars()
            .one_or_none()
        )

        if valid is None:
            raise InvalidDictValueError(f"QC state '{qc_state}' is invalid")

        return valid

    def valid_qc_type(self, qc_type: str) -> QcType:
        """
        Given a description of the QC type, returns an object that
        corresponds to a relevant row in the `qc_type` table.
        Raises a `ValidationError` if no corresponding record is found.
        """

        valid = (
            self.session.execute(select(QcType).where(QcType.qc_type == qc_type))
            .scalars()
            .one_or_none()
        )

        if valid is None:
            raise InvalidDictValueError(f"QC type '{qc_type}' is invalidxs")

        return valid

    def current_qc_state(self, qc_type: str = "sequencing") -> QcState | None:
        """
        Returns a current record for the product assosioted with this
        instance in the `qc_state` table for QC. The type of OC is defined
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
                        QcState.id_qc_type == self.valid_qc_type(qc_type).id_qc_type,
                    )
                )
            )
            .scalars()
            .one_or_none()
        )

    def assign_qc_state(
        self,
        user: User,
        qc_state: str = "Claimed",
        qc_type: str = "sequencing",
        is_preliminary: bool = False,
        application: str = "LangQC",
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
        record does not exist and the `qc_type` attribure of this method defines the
        library QC type, a new database record is created.

        The method does not enforce any particular order of assigning QC states,
        neither it mandates that all QC assignments for the entity should be
        performed by the same user.

        A `ValidationError` is raised if the values of either `qc_state` or `qc_type`
        atributes are invalid.

        For each new or updated record in the `qc_state` row table a new record is
        created in the `qc_state_hist` table.

        If a record for the product defined by this instance is not present in the
        `seq_product` table, it is created alongside corresponding records in the
        `sub_product` and `product_layout` tables.
        """

        state = self.current_qc_state(qc_type)
        if (
            (state is not None)
            and (state.qc_state.state == qc_state)
            and (state.qc_state.is_preliminary == is_preliminary)
        ):
            # Do not update the state if it has not changed.
            # Return early, nothing more to do.
            return state

        valid_qc_state = self.valid_qc_state_dict(qc_state)

        # TODO: 'Claimed' and 'On hold' states cannot be final - enforce

        time = datetime.utcnow()
        values = {
            "id_qc_state_dict": valid_qc_state.id_qc_state_dict,
            "is_preliminary": is_preliminary,
            "id_user": user.id_user,
            "created_by": application,
            "date_updated": time,
        }

        if state is not None:
            state.update(values)
        else:
            # TODO: cache all qc types, this is a second call
            vaid_qc_type = self.valid_qc_type(qc_type)
            values["id_seq_product"] = self.seq_product.id_seq_product
            values["id_qc_type"] = vaid_qc_type.id_qc_type
            values["date_created"] = time
            state = QcState(**values)
            self.session.add(state)

        self.session.add(self._new_state_hist(state))
        self.session.commit()

        return state

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

    def _new_state_hist(self, qc_state: QcState) -> QcStateHist:

        data = {}
        for column_name in qc_state.__dict__:
            if (column_name.startswith("_") is False) and (
                column_name != "id_qc_state"
            ):
                data[column_name] = qc_state.__getattribute__(column_name)

        return QcStateHist(**data)
