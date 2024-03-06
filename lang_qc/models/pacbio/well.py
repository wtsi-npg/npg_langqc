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
from typing import Any, Optional

from pydantic import Field, model_validator
from pydantic.dataclasses import dataclass

from lang_qc.db.mlwh_schema import PacBioRunWellMetrics
from lang_qc.models.pacbio.experiment import PacBioExperiment
from lang_qc.models.pacbio.qc_data import QCDataWell
from lang_qc.models.pager import PagedResponse
from lang_qc.models.qc_state import QcState


def get_field_names(cls):
    """Returns a list of field names for a class given as an argument.

    The fields that can only be used at the object initialisation step
    are excluded. For fields, which have a validation_alias defined,
    this alias is returned rather than the field name.
    """

    field_names = []
    for field_name in cls.__dataclass_fields__:
        field = cls.__dataclass_fields__[field_name]
        if field.default.init_var is True:
            continue
        name = field.default.validation_alias
        if name is None:
            name = field.name
        field_names.append(name)
    return field_names


@dataclass(kw_only=True, frozen=True)
class PacBioWell:
    """A basic response model for a single PacBio well.

    `run_name`, `label`, `plate_number`, and `id_product` fields uniquely
    identify the well. The model also has fields that reflect the time line
    of the run and information about a PacBio instrument. The optional
    `qc_state  field might contain the current QC state of the well.

    The best way to instantiate the model is via the constructor, supplying
    the an ORM object representing a database row with information about
    the well and, optionally, the model representing the current QC state.

    Examples:
        well_model = PacBioWell(db_well=well_row)
        well_model = PacBioWell(db_well=well_row, qc_state=current_qc_state)

    Mapping of the database values to this model's fields is performed by
    a pre `__init__` hook. To enable automatic mapping, some fields of this
    model have `validation_alias` set.
    """

    db_well: PacBioRunWellMetrics = Field(init_var=True)

    # Well identifies.
    id_product: str = Field(
        title="Product identifier", validation_alias="id_pac_bio_product"
    )
    label: str = Field(
        title="Well label",
        description="The label of the PacBio well",
        validation_alias="well_label",
    )
    plate_number: Optional[int] = Field(
        default=None,
        title="Plate number",
        description="Plate number, relevant for Revio instruments only",
    )
    run_name: str = Field(
        title="Run name",
        description="PacBio run name as registered in LIMS",
        validation_alias="pac_bio_run_name",
    )
    # Run and well tracking information from SMRT Link
    run_start_time: Optional[datetime] = Field(
        default=None, title="Run start time", validation_alias="run_start"
    )
    run_complete_time: Optional[datetime] = Field(
        default=None, title="Run complete time", validation_alias="run_complete"
    )
    well_start_time: Optional[datetime] = Field(
        default=None, title="Well start time", validation_alias="well_start"
    )
    well_complete_time: Optional[datetime] = Field(
        default=None, title="Well complete time", validation_alias="well_complete"
    )
    run_status: Optional[str] = Field(default=None, title="Current PacBio run status")
    well_status: Optional[str] = Field(default=None, title="Current PacBio well status")
    instrument_name: Optional[str] = Field(default=None, title="Instrument name")
    instrument_type: Optional[str] = Field(default=None, title="Instrument type")

    qc_state: Optional[QcState] = Field(
        default=None,
        title="Current QC state of this well",
        description="""
        Current QC state of this well as a QcState pydantic model.
        The well might have no QC state assigned. Whether the QC state is
        available depends on the lifecycle stage of this well.
        """,
    )

    @model_validator(mode="before")
    def pre_root(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Populates this object with the run and well tracking information
        from a database row that is passed as an argument.
        """

        # https://github.com/pydantic/pydantic-core/blob/main/python/pydantic_core/_pydantic_core.pyi
        mlwh_db_row: PacBioRunWellMetrics = values.kwargs["db_well"]

        column_names = [column.key for column in PacBioRunWellMetrics.__table__.columns]

        assigned = dict()
        for field_name in get_field_names(cls):
            if field_name in column_names:
                assigned[field_name] = getattr(mlwh_db_row, field_name)

        if "qc_state" in values.kwargs:
            assigned["qc_state"] = values.kwargs["qc_state"]

        return assigned


class PacBioPagedWells(PagedResponse, extra="forbid"):
    """A response model for paged data about PacBio wells."""

    wells: list[PacBioWell] = Field(
        default=[],
        title="A list of PacBioWell objects",
        description="""
        A list of `PacBioWell` objects that corresponds to the page number
        and size specified by the `page_size` and `page_number` attributes.
        """,
    )


@dataclass(kw_only=True, frozen=True)
class PacBioWellFull(PacBioWell):
    """A full response model for a single PacBio well.

    The model has teh fields that uniquely define the well (`run_name`, `label`,
    `plate_number`, `id_product`), along with the laboratory experiment and
    sequence run tracking information, current QC state of this well and
    QC data for this well.

    Instance creation is described in the documentation of this class's parent
    `PacBioWell`.
    """

    metrics: QCDataWell = Field(
        title="Currently available QC data for well",
    )
    experiment_tracking: Optional[PacBioExperiment] = Field(
        default=None,
        title="Experiment tracking information",
        description="""
        Laboratory experiment tracking information for this well, if available.
        """,
    )

    @model_validator(mode="before")
    def pre_root(cls, values: dict[str, Any]) -> dict[str, Any]:

        assigned = super().pre_root(values)
        mlwh_db_row: PacBioRunWellMetrics = values.kwargs["db_well"]

        assigned["metrics"] = QCDataWell.from_orm(mlwh_db_row)

        product_metrics = mlwh_db_row.pac_bio_product_metrics
        experiment_info = [
            pbr for pbr in [pm.pac_bio_run for pm in product_metrics] if pbr is not None
        ]
        # Occasionally product rows are not linked to LIMS rows.
        # Go for all or nothing, do not supply incomplete data.
        if len(experiment_info) and (len(experiment_info) == len(product_metrics)):
            assigned["experiment_tracking"] = PacBioExperiment.from_orm(experiment_info)

        return assigned
