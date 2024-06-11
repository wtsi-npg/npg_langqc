# -*- coding: utf-8 -*-
#
# Copyright © 2023 Genome Research Ltd. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# @author mgcam <mg8@sanger.ac.uk>

from sqlalchemy import Column, Computed, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT as mysqlBIGINT
from sqlalchemy.dialects.mysql import CHAR as mysqlCHAR
from sqlalchemy.dialects.mysql import FLOAT as mysqlFLOAT
from sqlalchemy.dialects.mysql import INTEGER as mysqlINTEGER
from sqlalchemy.dialects.mysql import SMALLINT as mysqlSMALLINT
from sqlalchemy.dialects.mysql import TINYINT as mysqlTINYINT
from sqlalchemy.dialects.mysql import VARCHAR as mysqlVARCHAR
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """
    A base class for declarative class definitions for the ml warehouse database.
    """

    def get_row_description(self, fields: list[str]) -> str:
        """
        Returns a printable representation of the database table row. Interprets
        a list of strings given as the `fields` argument as a list of column
        names. Combines the name of the class, names of the given columns
        and respective values into a row description. The columns for which
        the row has a NULL value are omitted from the description.
        """

        pairs = []
        for name in fields:
            value = self.__getattribute__(name)
            if value is not None:
                pairs.append(f"{name}={value}")
        description = ", ".join(pairs)
        return f"{self.__module__}.{self.__class__.__name__}: {description}"


class Sample(Base):
    __tablename__ = "sample"
    __table_args__ = (
        Index(
            "index_sample_on_id_sample_lims_and_id_lims",
            "id_sample_lims",
            "id_lims",
            unique=True,
        ),
    )

    id_sample_tmp = Column(
        mysqlINTEGER(10, unsigned=True),
        primary_key=True,
        comment="Internal to this database id, value can change",
    )
    id_lims = Column(
        String(10, "utf8_unicode_ci"),
        nullable=False,
        comment="LIM system identifier, e.g. CLARITY-GCLP, SEQSCAPE",
    )
    id_sample_lims = Column(
        String(20, "utf8_unicode_ci"),
        nullable=False,
        comment="LIMS-specific sample identifier",
    )
    consent_withdrawn = Column(
        mysqlTINYINT(1), nullable=False, server_default=text("'0'")
    )
    uuid_sample_lims = Column(
        String(36, "utf8_unicode_ci"), unique=True, comment="LIMS-specific sample uuid"
    )
    name = Column(String(255, "utf8_unicode_ci"), index=True)
    reference_genome = Column(String(255, "utf8_unicode_ci"))
    organism = Column(String(255, "utf8_unicode_ci"))
    accession_number = Column(String(50, "utf8_unicode_ci"), index=True)
    common_name = Column(String(255, "utf8_unicode_ci"))
    description = Column(Text(collation="utf8_unicode_ci"))
    taxon_id = Column(mysqlINTEGER(6, unsigned=True))
    sanger_sample_id = Column(String(255, "utf8_unicode_ci"), index=True)
    control = Column(mysqlTINYINT(1))
    supplier_name = Column(String(255, "utf8_unicode_ci"), index=True)
    public_name = Column(String(255, "utf8_unicode_ci"))
    strain = Column(String(255, "utf8_unicode_ci"))
    control_type = Column(String(255, "utf8_unicode_ci"))
    sample_type = Column(String(255, "utf8_unicode_ci"))

    pac_bio_run = relationship("PacBioRun", back_populates="sample")


class Study(Base):
    __tablename__ = "study"
    __table_args__ = (
        Index(
            "study_id_lims_id_study_lims_index", "id_lims", "id_study_lims", unique=True
        ),
    )

    id_study_tmp = Column(
        mysqlINTEGER(10, unsigned=True),
        primary_key=True,
        comment="Internal to this database id, value can change",
    )
    id_lims = Column(
        String(10, "utf8_unicode_ci"),
        nullable=False,
        comment="LIM system identifier, e.g. GCLP-CLARITY, SEQSCAPE",
    )
    id_study_lims = Column(
        String(20, "utf8_unicode_ci"),
        nullable=False,
        comment="LIMS-specific study identifier",
    )
    remove_x_and_autosomes = Column(
        mysqlTINYINT(1), nullable=False, server_default=text("'0'")
    )
    aligned = Column(mysqlTINYINT(1), nullable=False, server_default=text("'1'"))
    separate_y_chromosome_data = Column(
        mysqlTINYINT(1), nullable=False, server_default=text("'0'")
    )
    uuid_study_lims = Column(
        String(36, "utf8_unicode_ci"), unique=True, comment="LIMS-specific study uuid"
    )
    name = Column(String(255, "utf8_unicode_ci"), index=True)
    reference_genome = Column(String(255, "utf8_unicode_ci"))
    accession_number = Column(String(50, "utf8_unicode_ci"), index=True)
    description = Column(Text(collation="utf8_unicode_ci"))
    contains_human_dna = Column(mysqlTINYINT(1), comment="Lane may contain human DNA")
    contaminated_human_dna = Column(
        mysqlTINYINT(1),
        comment="Human DNA in the lane is a contaminant and should be removed",
    )
    study_title = Column(String(255, "utf8_unicode_ci"))
    study_visibility = Column(String(255, "utf8_unicode_ci"))

    pac_bio_run = relationship("PacBioRun", back_populates="study")


class PacBioRun(Base):
    __tablename__ = "pac_bio_run"
    __table_args__ = (
        Index(
            "unique_pac_bio_entry",
            "id_lims",
            "id_pac_bio_run_lims",
            "well_label",
            "comparable_tag_identifier",
            "comparable_tag2_identifier",
            "plate_number",
            unique=True,
        ),
    )

    id_pac_bio_tmp = Column(mysqlINTEGER(11), primary_key=True)
    last_updated = Column(DateTime, nullable=False, comment="Timestamp of last update")
    recorded_at = Column(
        DateTime, nullable=False, comment="Timestamp of warehouse update"
    )
    id_sample_tmp = Column(
        ForeignKey("sample.id_sample_tmp"),
        nullable=False,
        index=True,
        comment='Sample id, see "sample.id_sample_tmp"',
    )
    id_study_tmp = Column(
        ForeignKey("study.id_study_tmp"),
        nullable=False,
        index=True,
        comment='Sample id, see "study.id_study_tmp"',
    )
    id_pac_bio_run_lims = Column(
        String(20, "utf8_unicode_ci"),
        nullable=False,
        comment="Lims specific identifier for the pacbio run",
    )
    cost_code = Column(
        String(20, "utf8_unicode_ci"), nullable=False, comment="Valid WTSI cost-code"
    )
    id_lims = Column(
        String(10, "utf8_unicode_ci"), nullable=False, comment="LIM system identifier"
    )
    plate_barcode = Column(
        String(255, "utf8_unicode_ci"),
        nullable=True,
        comment="The human readable barcode for the plate loaded onto the machine",
    )
    plate_number = Column(
        mysqlINTEGER(),
        nullable=True,
        comment="""
        The number of the plate that goes onto the Revio sequencing machine.
        Necessary as an identifier for multi-plate support.
        """,
    )
    plate_uuid_lims = Column(
        String(36, "utf8_unicode_ci"), nullable=False, comment="The plate uuid"
    )
    well_label = Column(
        String(255, "utf8_unicode_ci"),
        nullable=False,
        comment="The well identifier for the plate, A1-H12",
    )
    well_uuid_lims = Column(
        String(36, "utf8_unicode_ci"), nullable=False, comment="The well uuid"
    )
    pac_bio_library_tube_id_lims = Column(
        String(255, "utf8_unicode_ci"),
        nullable=False,
        comment="LIMS specific identifier for originating library tube",
    )
    pac_bio_library_tube_uuid = Column(
        String(255, "utf8_unicode_ci"),
        nullable=False,
        comment="The uuid for the originating library tube",
    )
    pac_bio_library_tube_name = Column(
        String(255, "utf8_unicode_ci"),
        nullable=False,
        comment="The name of the originating library tube",
    )
    pac_bio_run_uuid = Column(
        String(36, "utf8_unicode_ci"), comment="Uuid identifier for the pacbio run"
    )
    tag_identifier = Column(
        String(30, "utf8_unicode_ci"),
        comment="Tag index within tag set, NULL if untagged",
    )
    tag_sequence = Column(String(30, "utf8_unicode_ci"), comment="Tag sequence for tag")
    tag_set_id_lims = Column(
        String(20, "utf8_unicode_ci"),
        comment="LIMs-specific identifier of the tag set for tag",
    )
    tag_set_name = Column(
        String(100, "utf8_unicode_ci"), comment="WTSI-wide tag set name for tag"
    )
    tag2_sequence = Column(String(30, "utf8_unicode_ci"))
    tag2_set_id_lims = Column(String(20, "utf8_unicode_ci"))
    tag2_set_name = Column(String(100, "utf8_unicode_ci"))
    tag2_identifier = Column(String(30, "utf8_unicode_ci"))
    pac_bio_library_tube_legacy_id = Column(
        mysqlINTEGER(11), comment="Legacy library_id for backwards compatibility."
    )
    library_created_at = Column(DateTime, comment="Timestamp of library creation")
    pac_bio_run_name = Column(String(255, "utf8_unicode_ci"), comment="Name of the run")
    pipeline_id_lims = Column(
        String(60, "utf8_unicode_ci"),
        comment="""LIMS-specific pipeline identifier that unambiguously defines
        library type (eg. Sequel-v1, IsoSeq-v1)""",
    )
    comparable_tag_identifier = Column(
        String(255, "utf8_unicode_ci"),
        Computed("(ifnull(`tag_identifier`,-(1)))", persisted=False),
    )
    comparable_tag2_identifier = Column(
        String(255, "utf8_unicode_ci"),
        Computed("(ifnull(`tag2_identifier`,-(1)))", persisted=False),
    )
    pac_bio_library_tube_barcode = Column(
        String(255), comment="The barcode of the originating library tube"
    )

    sample = relationship("Sample", back_populates="pac_bio_run")
    study = relationship("Study", back_populates="pac_bio_run")
    pac_bio_product_metrics = relationship(
        "PacBioProductMetrics", back_populates="pac_bio_run"
    )


class PacBioRunWellMetrics(Base):
    __tablename__ = "pac_bio_run_well_metrics"
    __table_args__ = (
        Index(
            "pac_bio_metrics_run_well",
            "pac_bio_run_name",
            "well_label",
            "plate_number",
            unique=True,
        ),
        Index("pb_rw_qc_state_index", "qc_seq_state", "qc_seq_state_is_final"),
        {
            "comment": "Status and run information by well and some basic QC data from "
            "SMRT Link"
        },
    )

    id_pac_bio_rw_metrics_tmp = Column(mysqlINTEGER(11), primary_key=True)
    pac_bio_run_name = Column(
        mysqlVARCHAR(255, charset="utf8", collation="utf8_unicode_ci"),
        nullable=False,
        comment="Lims specific identifier for the pacbio run",
    )
    well_label = Column(
        mysqlVARCHAR(255, charset="utf8", collation="utf8_unicode_ci"),
        nullable=False,
        comment="The well identifier for the plate, A1-H12",
    )
    plate_number = Column(
        mysqlINTEGER(),
        nullable=True,
        comment="""
        The number of the plate that goes onto the Revio sequencing machine.
        Necessary as an identifier for multi-plate support.
        """,
    )
    instrument_type = Column(
        mysqlVARCHAR(32, charset="utf8", collation="utf8_unicode_ci"),
        nullable=False,
        comment="The instrument type e.g. Sequel",
    )
    id_pac_bio_product = Column(
        mysqlCHAR(64, charset="utf8", collation="utf8_unicode_ci"),
        nullable=False,
        unique=True,
        comment="Product id",
    )
    qc_seq_state = Column(String(255), comment="Current sequencing QC state")
    qc_seq_state_is_final = Column(
        mysqlTINYINT(1),
        comment="A flag marking the sequencing QC state as final (1) or not final (0)",
    )
    qc_seq_date = Column(
        DateTime,
        index=True,
        comment="The date the current sequencing QC state was assigned",
    )
    qc_seq = Column(
        mysqlTINYINT(1),
        comment="The final sequencing QC outcome as 0(failed), 1(passed) or NULL",
    )
    instrument_name = Column(
        mysqlVARCHAR(32, charset="utf8", collation="utf8_unicode_ci"),
        comment="The instrument name e.g. SQ54097",
    )
    chip_type = Column(
        mysqlVARCHAR(32, charset="utf8", collation="utf8_unicode_ci"),
        comment="The chip type e.g. 8mChip",
    )
    sl_hostname = Column(
        mysqlVARCHAR(255, charset="utf8", collation="utf8_unicode_ci"),
        comment="SMRT Link server hostname",
    )
    sl_run_uuid = Column(
        mysqlVARCHAR(36, charset="utf8", collation="utf8_unicode_ci"),
        comment="SMRT Link specific run uuid",
    )
    sl_ccs_uuid = Column(
        mysqlVARCHAR(36, charset="utf8", collation="utf8_unicode_ci"),
        comment="SMRT Link specific ccs dataset uuid",
    )
    ts_run_name = Column(
        mysqlVARCHAR(32, charset="utf8", collation="utf8_unicode_ci"),
        comment="The PacBio run name",
    )
    movie_name = Column(
        mysqlVARCHAR(32, charset="utf8", collation="utf8_unicode_ci"),
        index=True,
        comment="The PacBio movie name",
    )
    movie_minutes = Column(
        mysqlSMALLINT(5, unsigned=True),
        comment="Movie time (collection time) in minutes",
    )
    created_by = Column(
        mysqlVARCHAR(32, charset="utf8", collation="utf8_unicode_ci"),
        comment="Created by user name recorded in SMRT Link",
    )
    binding_kit = Column(
        mysqlVARCHAR(255, charset="utf8", collation="utf8_unicode_ci"),
        comment="Binding kit version",
    )
    sequencing_kit = Column(
        mysqlVARCHAR(255, charset="utf8", collation="utf8_unicode_ci"),
        comment="Sequencing kit version",
    )
    sequencing_kit_lot_number = Column(
        mysqlVARCHAR(255, charset="utf8", collation="utf8_unicode_ci"),
        comment="Sequencing Kit lot number",
    )
    cell_lot_number = Column(String(32), comment="SMRT Cell Lot Number")
    ccs_execution_mode = Column(
        mysqlVARCHAR(32, charset="utf8", collation="utf8_unicode_ci"),
        index=True,
        comment="The PacBio ccs exection mode e.g. OnInstument, OffInstument or None",
    )
    demultiplex_mode = Column(
        String(32), comment="Demultiplexing mode e.g. OnInstument, OffInstument or None"
    )
    include_kinetics = Column(
        mysqlTINYINT(1, unsigned=True),
        comment="Include kinetics information where ccs is run",
    )
    hifi_only_reads = Column(
        mysqlTINYINT(1, unsigned=True),
        comment="""CCS was run on the instrument and only HiFi reads were included
        in the export from the instrument""",
    )
    heteroduplex_analysis = Column(
        mysqlTINYINT(1, unsigned=True),
        comment="Analysis has been run on the instrument to detect and resolve heteroduplex reads",
    )
    loading_conc = Column(
        mysqlFLOAT(unsigned=True), comment="SMRT Cell loading concentration (pM)"
    )
    run_start = Column(DateTime, comment="Timestamp of run started")
    run_complete = Column(DateTime, index=True, comment="Timestamp of run complete")
    run_transfer_complete = Column(
        DateTime, comment="Timestamp of run transfer complete"
    )
    run_status = Column(
        String(32),
        comment="Last recorded status, primarily to explain runs not completed.",
    )
    well_start = Column(DateTime, comment="Timestamp of well started")
    well_complete = Column(DateTime, index=True, comment="Timestamp of well complete")
    well_status = Column(
        String(32),
        comment="Last recorded status, primarily to explain wells not completed.",
    )
    chemistry_sw_version = Column(
        mysqlVARCHAR(32, charset="utf8", collation="utf8_unicode_ci"),
        comment="The PacBio chemistry software version",
    )
    instrument_sw_version = Column(
        mysqlVARCHAR(32, charset="utf8", collation="utf8_unicode_ci"),
        comment="The PacBio instrument software version",
    )
    primary_analysis_sw_version = Column(
        mysqlVARCHAR(32, charset="utf8", collation="utf8_unicode_ci"),
        comment="The PacBio primary analysis software version",
    )
    control_num_reads = Column(
        mysqlINTEGER(10, unsigned=True), comment="The number of control reads"
    )
    control_concordance_mean = Column(
        mysqlFLOAT(8, 6, unsigned=True),
        comment="""The average concordance between the control raw reads
        and the control reference sequence""",
    )
    control_concordance_mode = Column(
        mysqlFLOAT(unsigned=True),
        comment="""The modal value from the concordance between the control
        raw reads and the control reference sequence""",
    )
    control_read_length_mean = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="The mean polymerase read length of the control reads",
    )
    local_base_rate = Column(
        mysqlFLOAT(8, 6, unsigned=True),
        comment="The average base incorporation rate, excluding polymerase pausing events",
    )
    polymerase_read_bases = Column(
        mysqlBIGINT(20, unsigned=True),
        comment="""Calculated by multiplying the number of productive (P1) ZMWs
        by the mean polymerase read length""",
    )
    polymerase_num_reads = Column(
        mysqlINTEGER(10, unsigned=True), comment="The number of polymerase reads"
    )
    polymerase_read_length_mean = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="The mean high-quality read length of all polymerase reads",
    )
    polymerase_read_length_n50 = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="""Fifty percent of the trimmed read length of all polymerase
        reads are longer than this value""",
    )
    insert_length_mean = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="The average subread length, considering only the longest subread from each ZMW",
    )
    insert_length_n50 = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="""Fifty percent of the subreads are longer than this value when considering
        only the longest subread from each ZMW""",
    )
    unique_molecular_bases = Column(
        mysqlBIGINT(20, unsigned=True), comment="The unique molecular yield in bp"
    )
    productive_zmws_num = Column(
        mysqlINTEGER(10, unsigned=True), comment="Number of productive ZMWs"
    )
    p0_num = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="Number of empty ZMWs with no high quality read detected",
    )
    p1_num = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="Number of ZMWs with a high quality read detected",
    )
    p2_num = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="Number of other ZMWs, signal detected but no high quality read",
    )
    adapter_dimer_percent = Column(
        mysqlFLOAT(5, 2, unsigned=True),
        comment="The percentage of pre-filter ZMWs which have observed inserts of 0-10 bp",
    )
    short_insert_percent = Column(
        mysqlFLOAT(5, 2, unsigned=True),
        comment="The percentage of pre-filter ZMWs which have observed inserts of 11-100 bp",
    )
    hifi_read_bases = Column(
        mysqlBIGINT(20, unsigned=True), comment="The number of HiFi bases"
    )
    hifi_num_reads = Column(
        mysqlINTEGER(10, unsigned=True), comment="The number of HiFi reads"
    )
    hifi_read_length_mean = Column(
        mysqlINTEGER(10, unsigned=True), comment="The mean HiFi read length"
    )
    hifi_read_quality_median = Column(
        mysqlSMALLINT(5, unsigned=True), comment="The median HiFi base quality"
    )
    hifi_number_passes_mean = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="The mean number of passes per HiFi read",
    )
    hifi_low_quality_read_bases = Column(
        mysqlBIGINT(20, unsigned=True),
        comment="The number of HiFi bases filtered due to low quality (<Q20)",
    )
    hifi_low_quality_num_reads = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="The number of HiFi reads filtered due to low quality (<Q20)",
    )
    hifi_low_quality_read_length_mean = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="The mean length of HiFi reads filtered due to low quality (<Q20)",
    )
    hifi_low_quality_read_quality_median = Column(
        mysqlSMALLINT(5, unsigned=True),
        comment="The median base quality of HiFi bases filtered due to low quality (<Q20)",
    )
    hifi_barcoded_reads = Column(
        mysqlINTEGER(10, unsigned=True),
        comment="Number of reads with an expected barcode in demultiplexed HiFi data",
    )
    hifi_bases_in_barcoded_reads = Column(
        mysqlBIGINT(20, unsigned=True),
        comment="Number of bases in reads with an expected barcode in demultiplexed HiFi data",
    )

    pac_bio_product_metrics = relationship(
        "PacBioProductMetrics", back_populates="pac_bio_run_well_metrics"
    )

    """Custom or customised methods are added below"""

    def __repr__(self):
        """Returns a printable representation of the database row"""

        return self.get_row_description(
            ["pac_bio_run_name", "well_label", "plate_number", "id_pac_bio_product"]
        )

    def get_experiment_info(self) -> list[PacBioRun]:
        """Returns a list of PacBioRun mlwh database rows.

        Returns LIMS information about the PacBio experiment
        for this well, one pac_bio_run table row per sample
        (product) in the well.

        If any or all of the pac_bio_product_metrics rows linked
        to this well record are not linked to the pac_bio_run
        table, and empty array is returned, thus preventing incomplete
        data being supplied to the client.
        """
        product_metrics = self.pac_bio_product_metrics
        experiment_info = [
            pbr for pbr in [pm.pac_bio_run for pm in product_metrics] if pbr is not None
        ]
        if len(experiment_info) != len(product_metrics):
            experiment_info = []

        return experiment_info


class PacBioProductMetrics(Base):
    __tablename__ = "pac_bio_product_metrics"
    __table_args__ = (
        Index(
            "pac_bio_metrics_product",
            "id_pac_bio_tmp",
            "id_pac_bio_rw_metrics_tmp",
            unique=True,
        ),
        {
            "comment": "A linking table for the pac_bio_run and pac_bio_run_well_metrics "
            "tables with a potential for adding per-product QC data"
        },
    )

    id_pac_bio_pr_metrics_tmp = Column(mysqlINTEGER(11), primary_key=True)
    id_pac_bio_rw_metrics_tmp = Column(
        ForeignKey(
            "pac_bio_run_well_metrics.id_pac_bio_rw_metrics_tmp", ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
        comment='''PacBio run well metrics id, see
        "pac_bio_run_well_metrics.id_pac_bio_rw_metrics_tmp"''',
    )
    id_pac_bio_tmp = Column(
        ForeignKey("pac_bio_run.id_pac_bio_tmp", ondelete="SET NULL"),
        comment='PacBio run id, see "pac_bio_run.id_pac_bio_tmp"',
    )
    id_pac_bio_product = Column(
        mysqlCHAR(64, charset="utf8", collation="utf8_unicode_ci"),
        nullable=False,
        unique=True,
        comment="Product id",
    )
    qc = Column(
        mysqlTINYINT(1),
        index=True,
        comment="The final QC outcome of the product as 0(failed), 1(passed) or NULL",
    )
    hifi_read_bases = Column(
        mysqlBIGINT(unsigned=True), nullable=True, comment="The number of HiFi bases"
    )
    hifi_num_reads = Column(
        mysqlINTEGER(unsigned=True), nullable=True, comment="The number of HiFi reads"
    )
    hifi_read_length_mean = Column(
        mysqlINTEGER(unsigned=True), nullable=True, comment="The mean HiFi read length"
    )
    barcode_quality_score_mean = Column(
        mysqlSMALLINT(unsigned=True),
        nullable=True,
        comment="The mean barcode HiFi quality score",
    )
    hifi_bases_percent = Column(
        mysqlFLOAT(),
        nullable=True,
        comment="The HiFi bases expressed as a percentage of the total HiFi bases",
    )

    pac_bio_run_well_metrics = relationship(
        "PacBioRunWellMetrics", back_populates="pac_bio_product_metrics"
    )
    pac_bio_run = relationship("PacBioRun", back_populates="pac_bio_product_metrics")
