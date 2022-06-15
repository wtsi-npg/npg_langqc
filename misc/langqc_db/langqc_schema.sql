-- Tables defining a sequencing product.
-- These definitions are created with the PacBio and ONT platforms
-- in mind, but, in principle, should be usable for the Illumina
-- and any other platform.

CREATE TABLE `seq_platform_dict` (
  `id_seq_platform_dict` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(10) NOT NULL,
  `description` varchar(255) NOT NULL,
  `iscurrent` boolean NOT NULL DEFAULT '1',
  PRIMARY KEY (`id_seq_platform_dict`),
  UNIQUE KEY `unique_seq_platform_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `sub_product_attr` (
  `id_attr` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `attr_name` varchar(20) NOT NULL,
  `description` varchar(255) NOT NULL,
  PRIMARY KEY (`id_attr`),
  UNIQUE KEY `unique_subpr_attr` (`attr_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `sub_product` (
  `id_sub_product` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `id_attr_one` int(11) unsigned NOT NULL,
  `value_attr_one` varchar(20) NOT NULL,
  `id_attr_two` int(11) unsigned NOT NULL,
  `value_attr_two` varchar(20) NOT NULL,
  `tags` varchar(255) DEFAULT NULL,
  `properties` JSON NOT NULL,
  `properties_digest` char(64) NOT NULL,
  PRIMARY KEY (`id_sub_product`),
  UNIQUE KEY `unique_sub_product_digest` (`properties_digest`),
  KEY `sub_product_value_attr_one` (`value_attr_one`),
  KEY `sub_product_value_attr_two` (`value_attr_two`),
  KEY `sub_product_tags` (`tags`),
  CONSTRAINT `fk_subproduct_attr1` FOREIGN KEY (`id_attr_one`) \
    REFERENCES `sub_product_attr` (`id_attr`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_subproduct_attr2` FOREIGN KEY (`id_attr_two`) \
    REFERENCES `sub_product_attr` (`id_attr`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `seq_product` (
  `id_seq_product` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `id_product` char(64) NOT NULL,
  `id_seq_platform_dict` int(11) unsigned NOT NULL,
  `has_seq_data` boolean DEFAULT 1,
  PRIMARY KEY (`id_seq_product`),
  UNIQUE KEY `unique_product` (`id_product`),
  CONSTRAINT `fk_subproduct_seq_pl` FOREIGN KEY (`id_seq_platform_dict`) \
    REFERENCES `seq_platform_dict` (`id_seq_platform_dict`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `product_layout` (
  `id_product_layout` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `id_seq_product` bigint(20) unsigned NOT NULL,
  `id_sub_product` bigint(20) unsigned NOT NULL,
  PRIMARY KEY (`id_product_layout`),
  UNIQUE KEY `unique_product_layout` (`id_seq_product`, `id_sub_product`),
  CONSTRAINT `fk_product_layout_seqpr` FOREIGN KEY (`id_seq_product`) \
    REFERENCES `seq_product` (`id_seq_product`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_product_layout_subpr` FOREIGN KEY (`id_sub_product`) \
    REFERENCES `sub_product` (`id_sub_product`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- A very simple user representation.

CREATE TABLE `user` (
  `id_user` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(12) NOT NULL,
  `date_created` datetime DEFAULT CURRENT_TIMESTAMP \
    COMMENT 'Datetime the user record was created',
  `date_updated` datetime DEFAULT CURRENT_TIMESTAMP \
    ON UPDATE CURRENT_TIMESTAMP \
    COMMENT 'Datetime the user record was created or changed',
  `iscurrent` boolean NOT NULL DEFAULT '1',
  PRIMARY KEY (`id_user`),
  UNIQUE KEY `unique_user` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Tables defining QC outcomes (pass, fail, etc.) for the products.

CREATE TABLE `qc_type_dict` (
  `id_qc_type_dict` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `qc_type` varchar(10) NOT NULL,
  `description` varchar(255) NOT NULL,
  PRIMARY KEY (`id_qc_type_dict`),
  UNIQUE KEY `unique_qc_type_dict` (`qc_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `qc_outcome_dict` (
  `id_qc_outcome_dict` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `outcome` varchar(255) NOT NULL,
  `short_outcome` tinyint(1) unsigned DEFAULT NULL,
  PRIMARY KEY (`id_qc_outcome_dict`),
  UNIQUE KEY `unique_qc_outcome_dict` (`outcome`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `qc_outcome` (
  `id_qc_outcome` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `id_seq_product` bigint(20) unsigned NOT NULL,
  `id_user` int(11) unsigned NOT NULL,
  `id_qc_outcome_dict` int(11) unsigned NOT NULL,
  `id_qc_type_dict` int(11) unsigned NOT NULL,
  `is_preliminary` boolean DEFAULT 1,
  `created_by` varchar(20) NOT NULL,
  `date_created` datetime DEFAULT CURRENT_TIMESTAMP \
    COMMENT 'Datetime this record was created',
  `date_updated` datetime DEFAULT CURRENT_TIMESTAMP \
    ON UPDATE CURRENT_TIMESTAMP \
    COMMENT 'Datetime this record was created or changed',
  PRIMARY KEY (`id_qc_outcome`),
  UNIQUE KEY `unique_qc_outcome` (`id_seq_product`, `id_qc_type_dict`),
  CONSTRAINT `fk_qc_outcome_product` FOREIGN KEY (`id_seq_product`) \
    REFERENCES `seq_product` (`id_seq_product`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_qc_outcome_user` FOREIGN KEY (`id_user`) \
    REFERENCES `user` (`id_user`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_qc_outcome_outcome` FOREIGN KEY (`id_qc_outcome_dict`) \
    REFERENCES `qc_outcome_dict` (`id_qc_outcome_dict`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_qc_outcome_type` FOREIGN KEY (`id_qc_type_dict`) \
    REFERENCES `qc_type_dict` (`id_qc_type_dict`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `qc_outcome_hist` (
  `id_qc_outcome_hist` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `id_seq_product` bigint(20) unsigned NOT NULL,
  `id_user` int(11) unsigned NOT NULL,
  `id_qc_outcome_dict` int(11) unsigned NOT NULL,
  `id_qc_type_dict` int(11) unsigned NOT NULL,
  `is_preliminary` boolean DEFAULT 1,
  `created_by` varchar(20) NOT NULL,
  `date_created` datetime NOT NULL \
    COMMENT 'Datetime the original record was created',
  `date_updated` datetime NOT NULL \
    COMMENT 'Datetime the original record was created or changed',
  PRIMARY KEY (`id_qc_outcome_hist`),
  CONSTRAINT `fk_qc_outcomeh_product` FOREIGN KEY (`id_seq_product`) \
    REFERENCES `seq_product` (`id_seq_product`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_qc_outcomeh_user` FOREIGN KEY (`id_user`) \
    REFERENCES `user` (`id_user`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_qc_outcomeh_outcome` FOREIGN KEY (`id_qc_outcome_dict`) \
    REFERENCES `qc_outcome_dict` (`id_qc_outcome_dict`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_qc_outcomeh_type` FOREIGN KEY (`id_qc_type_dict`) \
    REFERENCES `qc_type_dict` (`id_qc_type_dict`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Annotations.

CREATE TABLE `annotation` (
  `id_annotation` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `id_user` int(11) unsigned NOT NULL,
  `date_created` datetime DEFAULT CURRENT_TIMESTAMP \
    COMMENT 'Datetime this record was created',
  `comment` text NOT NULL,
  `qc_specific` boolean DEFAULT 0,
  PRIMARY KEY (`id_annotation`),
  CONSTRAINT `fk_annotation_user` FOREIGN KEY (`id_user`) \
    REFERENCES `user` (`id_user`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `product_annotation` (
  `id_product_annotation` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `id_annotation` bigint(20) unsigned NOT NULL,
  `id_seq_product` bigint(20) unsigned NOT NULL,
  PRIMARY KEY (`id_product_annotation`),
  CONSTRAINT `fk_pr_annotation_annotation` FOREIGN KEY (`id_annotation`) \
    REFERENCES `annotation` (`id_annotation`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_pr_annotation_product` FOREIGN KEY (`id_seq_product`) \
    REFERENCES `seq_product` (`id_seq_product`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Statuses

CREATE TABLE `status_dict` (
  `id_status_dict` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `description` varchar(30) NOT NULL,
  `long_description` varchar(255) NOT NULL,
  `temporal_index` int unsigned NOT NULL,
  `iscurrent` boolean DEFAULT 1,
  PRIMARY KEY (`id_status_dict`),
  UNIQUE KEY `unique_status_dict_desc` (`description`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `status` (
  `id_status` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `id_user` int(11) unsigned NOT NULL,
  `date_created` datetime DEFAULT CURRENT_TIMESTAMP \
    COMMENT 'Datetime this record was created',
  `id_status_dict` int(11) unsigned NOT NULL,
  `id_seq_product` bigint(20) unsigned NOT NULL,
  `iscurrent` boolean DEFAULT 0,
  PRIMARY KEY (`id_status`),
  CONSTRAINT `fk_status_user` FOREIGN KEY (`id_user`) \
    REFERENCES `user` (`id_user`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_status_product` FOREIGN KEY (`id_seq_product`) \
    REFERENCES `seq_product` (`id_seq_product`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_status_status_dict` FOREIGN KEY (`id_status_dict`) \
    REFERENCES `status_dict` (`id_status_dict`) \
    ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

