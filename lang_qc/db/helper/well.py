# Copyright (c) 2022, 2023 Genome Research Ltd.
#
# Authors:
#   Marina Gourtovaia <mg8@sanger.ac.uk>
#   Kieron Taylor <kt19@sanger.ac.uk>
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
A collection of specific to PacBio platform helper functions
for interaction with the LangQC database.
"""

from npg_id_generation.pac_bio import PacBioEntity
from sqlalchemy import select
from sqlalchemy.orm import Session

from lang_qc.db.helper.qc import get_seq_product
from lang_qc.db.mlwh_schema import PacBioRunWellMetrics
from lang_qc.db.qc_schema import SeqPlatform, SeqProduct, SubProduct, SubProductAttr


def well_seq_product_find_or_create(
    session: Session, mlwh_well: PacBioRunWellMetrics
) -> SeqProduct:
    """
    Returns a pre-existing `lang_qc.db.qc_schema.SeqProduct` for
    a PacBio well given as a ml warehouse row record or creates
    a new one.
    """

    id_product = mlwh_well.id_pac_bio_product
    well_product = get_seq_product(session, id_product)
    if well_product is None:
        well_product = _create_well(
            session,
            id_product,
            mlwh_well.pac_bio_run_name,
            mlwh_well.well_label,
            mlwh_well.plate_number,
        )

    return well_product


def _create_well(
    session: Session,
    id_product: str,
    run_name: str,
    well_label: str,
    plate_number: int = None,
) -> SeqProduct:

    id_seq_platform = (
        session.execute(select(SeqPlatform).where(SeqPlatform.name == "PacBio"))
        .scalar_one()
        .id_seq_platform
    )
    product_attr_id_rn = (
        session.execute(
            select(SubProductAttr).where(SubProductAttr.attr_name == "run_name")
        )
        .scalar_one()
        .id_attr
    )
    product_attr_id_wl = (
        session.execute(
            select(SubProductAttr).where(SubProductAttr.attr_name == "well_label")
        )
        .scalar_one()
        .id_attr
    )
    product_attr_id_pn = (
        session.execute(
            select(SubProductAttr).where(SubProductAttr.attr_name == "plate_number")
        )
        .scalar_one()
        .id_attr
    )
    product_json = PacBioEntity(
        run_name=run_name, well_label=well_label, plate_number=plate_number
    ).json()

    # TODO: in future for composite products we have to check whether any of
    # the `sub_product` table entries we are linking to already exist.
    well_product = SeqProduct(
        id_product=id_product,
        id_seq_platform=id_seq_platform,
        sub_products=[
            SubProduct(
                id_attr_one=product_attr_id_rn,
                value_attr_one=run_name,
                id_attr_two=product_attr_id_wl,
                value_attr_two=well_label,
                id_attr_three=product_attr_id_pn,
                value_attr_three=str(plate_number),
                properties=product_json,
                properties_digest=id_product,
            )
        ],
    )
    session.add(well_product)
    session.commit()

    return well_product
