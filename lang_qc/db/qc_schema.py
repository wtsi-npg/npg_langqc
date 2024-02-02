# Copyright (c) 2022, 2023 Genome Research Ltd.
#
# Authors:
#   Adam Blanchet
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
# this program. If not, see <http://www.gnu.org/licenses/>.

from sqlalchemy import (
    CHAR,
    JSON,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TINYINT
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class QcStateDict(Base):
    __tablename__ = "qc_state_dict"

    id_qc_state_dict = Column(INTEGER, primary_key=True)
    state = Column(String(255), nullable=False, unique=True)
    outcome = Column(TINYINT)

    qc_state = relationship("QcState", back_populates="qc_state_dict")
    qc_state_hist = relationship("QcStateHist", back_populates="qc_state_dict")


class QcType(Base):
    __tablename__ = "qc_type"

    id_qc_type = Column(INTEGER, primary_key=True)
    qc_type = Column(String(10), nullable=False, unique=True)
    description = Column(String(255), nullable=False)

    qc_state = relationship("QcState", back_populates="qc_type")
    qc_state_hist = relationship("QcStateHist", back_populates="qc_type")


class SeqPlatform(Base):
    __tablename__ = "seq_platform"

    id_seq_platform = Column(INTEGER, primary_key=True)
    name = Column(String(10), nullable=False, unique=True)
    description = Column(String(255), nullable=False)
    iscurrent = Column(TINYINT(1), nullable=False, server_default=text("'1'"))

    seq_product = relationship("SeqProduct", back_populates="seq_platform")


class SubProductAttr(Base):
    __tablename__ = "sub_product_attr"

    id_attr = Column(INTEGER, primary_key=True)
    attr_name = Column(String(20), nullable=False, unique=True)
    description = Column(String(255), nullable=False)

    sub_product = relationship(
        "SubProduct",
        foreign_keys="[SubProduct.id_attr_one]",
        back_populates="sub_product_attr",
    )
    sub_product_ = relationship(
        "SubProduct",
        foreign_keys="[SubProduct.id_attr_two]",
        back_populates="sub_product_attr_",
    )
    sub_product__ = relationship(
        "SubProduct",
        foreign_keys="[SubProduct.id_attr_three]",
        back_populates="sub_product_attr__",
    )


class User(Base):
    __tablename__ = "user"

    id_user = Column(INTEGER, primary_key=True)
    username = Column(String(255), nullable=False, unique=True)
    iscurrent = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    date_created = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Datetime the user record was created",
    )
    date_updated = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        comment="Datetime the user record was created or changed",
    )

    annotation = relationship("Annotation", back_populates="user")
    qc_state = relationship("QcState", back_populates="user")
    qc_state_hist = relationship("QcStateHist", back_populates="user")


class Annotation(Base):
    __tablename__ = "annotation"
    __table_args__ = (
        ForeignKeyConstraint(["id_user"], ["user.id_user"], name="fk_annotation_user"),
    )

    id_annotation = Column(BIGINT, primary_key=True)
    id_user = Column(INTEGER, nullable=False, index=True)
    comment = Column(Text, nullable=False)
    date_created = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Datetime this record was created",
    )
    qc_specific = Column(TINYINT(1), server_default=text("'0'"))

    user = relationship("User", back_populates="annotation")
    product_annotation = relationship("ProductAnnotation", back_populates="annotation")


class SeqProduct(Base):
    __tablename__ = "seq_product"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_seq_platform"],
            ["seq_platform.id_seq_platform"],
            name="fk_subproduct_seq_pl",
        ),
    )

    id_seq_product = Column(BIGINT, primary_key=True)
    id_product = Column(CHAR(64), nullable=False, unique=True)
    id_seq_platform = Column(INTEGER, nullable=False, index=True)
    has_seq_data = Column(TINYINT(1), server_default=text("'1'"))

    seq_platform = relationship("SeqPlatform", back_populates="seq_product")
    product_annotation = relationship("ProductAnnotation", back_populates="seq_product")
    sub_products = relationship(
        "SubProduct", secondary="product_layout", back_populates="seq_products"
    )
    qc_state = relationship("QcState", back_populates="seq_product")
    qc_state_hist = relationship("QcStateHist", back_populates="seq_product")


class SubProduct(Base):
    __tablename__ = "sub_product"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_attr_one"], ["sub_product_attr.id_attr"], name="fk_subproduct_attr1"
        ),
        ForeignKeyConstraint(
            ["id_attr_two"], ["sub_product_attr.id_attr"], name="fk_subproduct_attr2"
        ),
        ForeignKeyConstraint(
            ["id_attr_three"], ["sub_product_attr.id_attr"], name="fk_subproduct_attr3"
        ),
    )

    id_sub_product = Column(BIGINT, primary_key=True)
    id_attr_one = Column(INTEGER, nullable=False, index=True)
    value_attr_one = Column(String(20), nullable=False, index=True)
    id_attr_two = Column(INTEGER, nullable=False, index=True)
    value_attr_two = Column(String(20), nullable=False, index=True)
    id_attr_three = Column(INTEGER, nullable=True, index=True)
    value_attr_three = Column(String(20), nullable=True, index=True)
    properties = Column(JSON, nullable=True)
    properties_digest = Column(CHAR(64), nullable=False, unique=True)
    tags = Column(String(255), index=True)

    sub_product_attr = relationship(
        "SubProductAttr", foreign_keys=[id_attr_one], back_populates="sub_product"
    )
    sub_product_attr_ = relationship(
        "SubProductAttr", foreign_keys=[id_attr_two], back_populates="sub_product_"
    )
    sub_product_attr__ = relationship(
        "SubProductAttr", foreign_keys=[id_attr_three], back_populates="sub_product__"
    )
    seq_products = relationship(
        "SeqProduct", secondary="product_layout", back_populates="sub_products"
    )


class ProductAnnotation(Base):
    __tablename__ = "product_annotation"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_annotation"],
            ["annotation.id_annotation"],
            name="fk_pr_annotation_annotation",
        ),
        ForeignKeyConstraint(
            ["id_seq_product"],
            ["seq_product.id_seq_product"],
            name="fk_pr_annotation_product",
        ),
    )

    id_product_annotation = Column(BIGINT, primary_key=True)
    id_annotation = Column(BIGINT, nullable=False, index=True)
    id_seq_product = Column(BIGINT, nullable=False, index=True)

    annotation = relationship("Annotation", back_populates="product_annotation")
    seq_product = relationship("SeqProduct", back_populates="product_annotation")


class ProductLayout(Base):
    __tablename__ = "product_layout"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_seq_product"],
            ["seq_product.id_seq_product"],
            name="fk_product_layout_seqpr",
        ),
        ForeignKeyConstraint(
            ["id_sub_product"],
            ["sub_product.id_sub_product"],
            name="fk_product_layout_subpr",
        ),
        Index("unique_product_layout", "id_seq_product", "id_sub_product", unique=True),
    )

    id_product_layout = Column(BIGINT, primary_key=True)
    id_seq_product = Column(BIGINT, nullable=False)
    id_sub_product = Column(BIGINT, nullable=False, index=True)


class QcState(Base):
    __tablename__ = "qc_state"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_qc_state_dict"],
            ["qc_state_dict.id_qc_state_dict"],
            name="fk_qc_state_state",
        ),
        ForeignKeyConstraint(["id_qc_type"], ["qc_type.id_qc_type"], name="fk_qc_type"),
        ForeignKeyConstraint(
            ["id_seq_product"],
            ["seq_product.id_seq_product"],
            name="fk_qc_state_product",
        ),
        ForeignKeyConstraint(["id_user"], ["user.id_user"], name="fk_qc_state_user"),
        Index("unique_qc_state", "id_seq_product", "id_qc_type", unique=True),
    )

    id_qc_state = Column(BIGINT, primary_key=True)
    id_seq_product = Column(BIGINT, nullable=False)
    id_user = Column(INTEGER, nullable=False, index=True)
    id_qc_state_dict = Column(INTEGER, nullable=False, index=True)
    id_qc_type = Column(INTEGER, nullable=False, index=True)
    created_by = Column(String(20), nullable=False)
    is_preliminary = Column(TINYINT(1), server_default=text("'1'"))
    date_created = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Datetime this record was created",
    )
    date_updated = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        comment="Datetime this record was created or changed",
    )

    qc_state_dict = relationship("QcStateDict", back_populates="qc_state")
    qc_type = relationship("QcType", back_populates="qc_state")
    seq_product = relationship("SeqProduct", back_populates="qc_state")
    user = relationship("User", back_populates="qc_state", uselist=False)


class QcStateHist(Base):
    __tablename__ = "qc_state_hist"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_qc_state_dict"],
            ["qc_state_dict.id_qc_state_dict"],
            name="fk_qc_stateh_state",
        ),
        ForeignKeyConstraint(
            ["id_qc_type"], ["qc_type.id_qc_type"], name="fk_qc_stateh_type"
        ),
        ForeignKeyConstraint(
            ["id_seq_product"],
            ["seq_product.id_seq_product"],
            name="fk_qc_stateh_product",
        ),
        ForeignKeyConstraint(["id_user"], ["user.id_user"], name="fk_qc_stateh_user"),
    )

    id_qc_state_hist = Column(BIGINT, primary_key=True)
    id_seq_product = Column(BIGINT, nullable=False, index=True)
    id_user = Column(INTEGER, nullable=False, index=True)
    id_qc_state_dict = Column(INTEGER, nullable=False, index=True)
    id_qc_type = Column(INTEGER, nullable=False, index=True)
    created_by = Column(String(20), nullable=False)
    date_created = Column(
        DateTime, nullable=False, comment="Datetime the original record was created"
    )
    date_updated = Column(
        DateTime,
        nullable=False,
        comment="Datetime the original record was created or changed",
    )
    is_preliminary = Column(TINYINT(1), server_default=text("'1'"))

    qc_state_dict = relationship("QcStateDict", back_populates="qc_state_hist")
    qc_type = relationship("QcType", back_populates="qc_state_hist")
    seq_product = relationship("SeqProduct", back_populates="qc_state_hist")
    user = relationship("User", back_populates="qc_state_hist")
