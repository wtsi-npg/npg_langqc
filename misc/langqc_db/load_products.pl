#!/usr/bin/env perl

use strict;
use warnings;
use lib qw/lib/;
use Digest::SHA qw/sha256_hex/;
use langqc::Schema;

my $schema = langqc::Schema->connect();

my $rs_sub_product = $schema->resultset('SubProduct');
my $rs_seq_product = $schema->resultset('SeqProduct');
my $rs_product_comp = $schema->resultset('ProductComposition');
my $rs_category_dict = $schema->resultset('ProductCategoryDict');

my $sub_products = [
  [qw(TRACTION-RUN-122 A1)],
  [qw(TRACTION-RUN-122 B1)],
  [qw(TRACTION-RUN-122 C1)],
  [qw(TRACTION-RUN-122 D1)],  
];

my $id_category_ni = $rs_category_dict->search(
  {category => 'library_notindexed'})->next->id_product_category_dict;

foreach my $sp (@{$sub_products}) {
  my $row_subp = $rs_sub_product->search(
    {value_attr_one => $sp->[0], value_attr_two => $sp->[1]})->next;
  my $row_seqp = $rs_seq_product->create(
    {id_product => $row_subp->digest, id_product_category_dict => $id_category_ni});
  $rs_product_comp->create(
    {id_seq_product => $row_seqp->id_seq_product,
     id_sub_product => $row_subp->id_sub_product});
}

$sub_products = [
  [qw(TRACTION-RUN-114 A1)],
  [qw(TRACTION-RUN-114 B1)]
];

my $id_category_i = $rs_category_dict->search(
  {category => 'library_indexed'})->next->id_product_category_dict;
my $id_category_b = $rs_category_dict->search(
  {category => 'bucket'})->next->id_product_category_dict;
my $id_category_m = $rs_category_dict->search(
  {category => 'merged'})->next->id_product_category_dict;

foreach my $sp (@{$sub_products}) {
  my @rows_subp = $rs_sub_product->search(
    {value_attr_one => $sp->[0], value_attr_two => $sp->[1]})->all;
  for my $row_subp (@rows_subp) {
    my $id_category = $row_subp->tag_one ? $id_category_i : $id_category_b; 
    my $row_seqp = $rs_seq_product->create(
      {id_product => $row_subp->digest, id_product_category_dict => $id_category}); 
    $rs_product_comp->create(
      {id_seq_product => $row_seqp->id_seq_product,
       id_sub_product => $row_subp->id_sub_product});
  }  
}

my @rows_subp = grep { $_->tag_one }
  $rs_sub_product->search({value_attr_one => 'TRACTION-RUN-114'})->all();
my $row_seqp = $rs_seq_product->create({id_product_category_dict => $id_category_m,
  id_product => sha256_hex(join q[], (sort map { $_->digest } @rows_subp))});
foreach my $row (@rows_subp) {
  $rs_product_comp->create(
    {id_seq_product => $row_seqp->id_seq_product,
     id_sub_product => $row->id_sub_product});
}

@rows_subp = $rs_sub_product->search(
  {value_attr_one => 'TRACTION-RUN-112'})->all();
foreach my $sp (@rows_subp) {
  my $id_category = $sp->tag_one ? $id_category_i : $id_category_b;
  my $row_seqp = $rs_seq_product->create(
    {id_product => $sp->digest, id_product_category_dict => $id_category});
  $rs_product_comp->create(
    {id_seq_product => $row_seqp->id_seq_product,
     id_sub_product => $sp->id_sub_product});
}

1;
