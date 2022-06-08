-- Dictionaries

insert into seq_platform_dict (`name`, `description`) values
  ('PacBio', 'Pacific Biosciences'),
  ('ONT', 'Oxford Nanopore Technologies'),
  ('Illumina', 'Illumina');

insert into sub_product_attr (`attr_name`, `description`, `id_seq_platform_dict`)
  values ('run_name', 'The name of the run according to LIMS', 1),
  ('well_label', 'Well (or cell) label', 1),
  ('flowcell_id', 'Flowcell id', 2),
  ('instrument_position', 'The position of the flowcell on the instrument', 2),
  ('id_run', 'Run id in the NPG run tracking system', 3),
  ('position', 'Illumina flowcell position (lane)', 3);

insert into product_category_dict (`category`, `description`) values
  ('library_indexed', 'A deplexed indexed libary'),
  ('library_notindexed', 'Not indexed library'),
  ('merged', 'Data merged from multiple sub products'),
  ('bucket', 'Data generated for the purpose of assessing sequencing process');

insert into user (`username`) values ('user1'), ('user2');

insert into qc_type_dict (`qc_type`, `description`) values
  ('library', 'Sample/library evaluation'),
  ('sequencing', 'Sequencing/instrument evaliation');

insert into qc_outcome_dict (`outcome`, `description`)
  values ('Accepted preliminary', 'Accepted preliminary'),
         ('Accepted final', 'Accepted final'),
         ('Rejected preliminary', 'Rejected preliminary'),
         ('Rejected final', 'Rejected final'),
         ('Undecided preliminary', 'Undecided preliminary'),
         ('Undecided final', 'Undecided final');

-- Data PacBio

insert into sub_product ( \
  `id_attr_one`, `value_attr_one`, `id_attr_two`, `value_attr_two`, \
  `id_seq_platform_dict`, `description`, `digest`) values
  (7, 'TRACTION-RUN-122', 8, 'A1', 1, '{"run_name":"TRACTION-RUN-122","well_label":"A1"}','d7114a452634a87252854a398c56a603268422febbabe24ab6ad3e6383a95b0a'),
  (7, 'TRACTION-RUN-122', 8, 'B1', 1, '{"run_name":"TRACTION-RUN-122","well_label":"B1"}', '10ff2b5815da40b98d0702c1afe60d156fd57fce00ae0ffd56495af10618247f'),
  (7, 'TRACTION-RUN-122', 8, 'C1', 1, '{"run_name":"TRACTION-RUN-122","well_label":"C1"}', '0fe151612fe66a54bd613ad4598080a6b277544fcecbb15a37f2f5c8d5710cf8'),
  (7, 'TRACTION-RUN-122', 8, 'D1', 1, '{"run_name":"TRACTION-RUN-122","well_label":"D1"}', 'bc8dfbe9359c0d31c02f25ea30823d05f9a4da326e9dec8407cc38075d53c862');

insert into sub_product ( \
  `id_attr_one`, `value_attr_one`, `id_attr_two`, `value_attr_two`, `tag_one`, \
  `id_seq_platform_dict`, `description`, `digest`) values
  (7, 'TRACTION-RUN-114', 8, 'A1', 'CGCATGACACGTGTGTT', 1, '{"run_name":"TRACTION-RUN-114","well_label":"A1","tag_one":"CGCATGACACGTGTGTT"}', 'eae073b2ed279ba48931754c26056c8a3a851464678569d54b3c27ce1017ae67'),
  (7, 'TRACTION-RUN-114', 8, 'B1', 'CATAGAGAGATAGTATT', 1, '{"run_name":"TRACTION-RUN-114","well_label":"B1","tag_one":"CATAGAGAGATAGTATT"}', 'e91252f1b10a38c523e6b6f572b5db206111af272b96a33b5ee97d9734eb3ea8'),
  (7, 'TRACTION-RUN-114', 8, 'A1', NULL, 1, '{"run_name":"TRACTION-RUN-114","well_label":"A1"}', '5a6f61b4fa2b6ed004947207ef98b98f9bf634f99960f6df5ccd57a078c0a647'),
  (7, 'TRACTION-RUN-114', 8, 'B1', NULL, 1, '{"run_name":"TRACTION-RUN-114","well_label":"B1"}', '1e866670136bd9067635734ea89c13ad43771e604565e3dad6a476c134f7e569'),
  (7, 'TRACTION-RUN-112', 8, 'A1', 'ATAGAGGC', 1, '{"run_name":"TRACTION-RUN-112","well_label":"A1","tag_one":"ATAGAGGC"}', 'fc2750dd5c44398bf5aa0cf14689918bf89d4aa366ebcd6e6b42087164b003d9'),
  (7, 'TRACTION-RUN-112', 8, 'A1', 'GGCTCTGA', 1, '{"run_name":"TRACTION-RUN-112","well_label":"A1","tag_one":"GGCTCTGA"}', 'c655a9d51e5e5b7c248feed8fb6bef65c1dbd2a249e1fba10a3b83582f58f292'),
  (7, 'TRACTION-RUN-112', 8, 'A1', NULL, 1, '{"run_name":"TRACTION-RUN-112","well_label":"A1"}', '360963343e80249cbbfdb96240810221bacf5d5c518ae7b6868043185d0982cc');
  

