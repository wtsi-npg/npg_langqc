#!/usr/bin/env perl

use strict;
use warnings;
use lib qw/lib/;
use Digest::SHA qw/sha256_hex/;
use langqc::Schema;

my $schema = langqc::Schema->connect();

my $rs_sub_product = $schema->resultset('SubProduct');
my $rs_seq_product = $schema->resultset('SeqProduct');
my $rs_product_layout = $schema->resultset('ProductLayout');
my $rs_platform = $schema->resultset('SeqPlatformDict');
my $rs_attrs = $schema->resultset('SubProductAttr');

my @raw_sub_products = (
  ['TRACTION-RUN-122', 'A1', undef, '{"run_name":"TRACTION-RUN-122","well_label":"A1"}',
   'd7114a452634a87252854a398c56a603268422febbabe24ab6ad3e6383a95b0a'],
  ['TRACTION-RUN-122', 'B1', undef, '{"run_name":"TRACTION-RUN-122","well_label":"B1"}',
    '10ff2b5815da40b98d0702c1afe60d156fd57fce00ae0ffd56495af10618247f'],
  ['TRACTION-RUN-122', 'C1', undef, '{"run_name":"TRACTION-RUN-122","well_label":"C1"}',
    '0fe151612fe66a54bd613ad4598080a6b277544fcecbb15a37f2f5c8d5710cf8'],
  ['TRACTION-RUN-122', 'D1', undef,'{"run_name":"TRACTION-RUN-122","well_label":"D1"}',
    'bc8dfbe9359c0d31c02f25ea30823d05f9a4da326e9dec8407cc38075d53c862'],
  ['TRACTION-RUN-114', 'A1', 'CGCATGACACGTGTGTT',
    '{"run_name":"TRACTION-RUN-114","well_label":"A1","tag_one":"CGCATGACACGTGTGTT"}',
    'eae073b2ed279ba48931754c26056c8a3a851464678569d54b3c27ce1017ae67'],
  ['TRACTION-RUN-114', 'B1', 'CATAGAGAGATAGTATT',
    '{"run_name":"TRACTION-RUN-114","well_label":"B1","tag_one":"CATAGAGAGATAGTATT"}',
    'e91252f1b10a38c523e6b6f572b5db206111af272b96a33b5ee97d9734eb3ea8'],
  ['TRACTION-RUN-112', 'A1', 'ATAGAGGC',
    '{"run_name":"TRACTION-RUN-112","well_label":"A1","tag_one":"ATAGAGGC"}',
    'fc2750dd5c44398bf5aa0cf14689918bf89d4aa366ebcd6e6b42087164b003d9'],
  ['TRACTION-RUN-112', 'A1', 'GGCTCTGA',
    '{"run_name":"TRACTION-RUN-112","well_label":"A1","tag_one":"GGCTCTGA"}',
    'c655a9d51e5e5b7c248feed8fb6bef65c1dbd2a249e1fba10a3b83582f58f292'],
  ['TRACTION-RUN-112', 'A1', undef,
    '{"run_name":"TRACTION-RUN-112","well_label":"A1"}',
    '360963343e80249cbbfdb96240810221bacf5d5c518ae7b6868043185d0982cc']
);

my $platform_id = $rs_platform->search({name => 'PacBio'})
                  ->next->id_seq_platform_dict;
my $name_attr_id = $rs_attrs->search({attr_name => 'run_name'})->next->id_attr;
my $well_attr_id = $rs_attrs->search({attr_name => 'well_label'})->next->id_attr; 

foreach my $p (@raw_sub_products) {
  my $data = {
    id_attr_one => $name_attr_id,
    id_attr_two => $well_attr_id,
    value_attr_one => $p->[0],
    value_attr_two => $p->[1],
    properties => $p->[3],
    properties_digest => $p->[4]
  };
  if ($p->[2]) {
    $data->{tags} = $p->[2];
  }
  $rs_sub_product->update_or_create($data);
}

my $sub_products = [
  [qw(TRACTION-RUN-122 A1)],
  [qw(TRACTION-RUN-122 B1)],
  [qw(TRACTION-RUN-122 C1)],
  [qw(TRACTION-RUN-122 D1)],  
];

foreach my $sp (@{$sub_products}) {
  my $row_subp = $rs_sub_product->search(
    {value_attr_one => $sp->[0], value_attr_two => $sp->[1]})->next;
  my $row_seqp = $rs_seq_product->update_or_create(
    {id_product => $row_subp->properties_digest,
     id_seq_platform_dict => $platform_id});
  $rs_product_layout->update_or_create(
    {id_seq_product => $row_seqp->id_seq_product,
     id_sub_product => $row_subp->id_sub_product});
}

$sub_products = [
  [qw(TRACTION-RUN-114 A1)],
  [qw(TRACTION-RUN-114 B1)]
];

foreach my $sp (@{$sub_products}) {
  my @rows_subp = $rs_sub_product->search(
    {value_attr_one => $sp->[0], value_attr_two => $sp->[1]})->all;
  for my $row_subp (@rows_subp) {
    my $row_seqp = $rs_seq_product->update_or_create(
      {id_product => $row_subp->properties_digest,
       id_seq_platform_dict => $platform_id}); 
    $rs_product_layout->update_or_create(
      {id_seq_product => $row_seqp->id_seq_product,
       id_sub_product => $row_subp->id_sub_product});
  }  
}

my @rows_subp = grep { $_->tags }
  $rs_sub_product->search({value_attr_one => 'TRACTION-RUN-114'})->all();
my $row_seqp = $rs_seq_product->update_or_create({
  id_seq_platform_dict => $platform_id,
  id_product => sha256_hex(
    join q[], (sort map { $_->properties_digest } @rows_subp))});
foreach my $row (@rows_subp) {
  $rs_product_layout->update_or_create(
    {id_seq_product => $row_seqp->id_seq_product,
     id_sub_product => $row->id_sub_product});
}

@rows_subp = $rs_sub_product->search(
  {value_attr_one => 'TRACTION-RUN-112'})->all();
foreach my $sp (@rows_subp) {
  my $row_seqp = $rs_seq_product->update_or_create(
    {id_product => $sp->properties_digest,
     has_seq_data => $sp->tags ? 1 : 0,
     id_seq_platform_dict => $platform_id});
  $rs_product_layout->update_or_create(
    {id_seq_product => $row_seqp->id_seq_product,
     id_sub_product => $sp->id_sub_product});
}

1;
