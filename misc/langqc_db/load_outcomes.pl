#!/usr/bin/env perl

use strict;
use warnings;
use lib qw/lib/;

use langqc::Schema;

my $schema = langqc::Schema->connect();

my $rs_annotation = $schema->resultset('Annotation');
my $rs_prod_annotation = $schema->resultset('ProductAnnotation');

########  Simple annotations ###########

my @annotations = ();
for my $n ((1 .. 6)) {
  push @annotations, $rs_annotation->create(
    {id_user => 1, comment => "Comment No $n"});
}

my $rs_sub_product = $schema->resultset('SubProduct');
my @rows =
  map { $_->seq_product }
  map { $_->product_layouts->next } 
  $rs_sub_product->search({value_attr_one => 'TRACTION-RUN-122'})->all();
foreach my $n (0 .. 3) {
  $rs_prod_annotation->create({id_annotation => $annotations[$n]->id_annotation,
                               id_seq_product => $rows[$n]->id_seq_product});
}

@rows =
  map { $_->seq_product }
  map { $_->product_layouts->next } 
  $rs_sub_product->search({value_attr_one => 'TRACTION-RUN-112'})->all();
foreach my $row (@rows) {
  my $a_index = $row->product_layouts->next->sub_product->tags ? 4 : 5;
  $rs_prod_annotation->update_or_create({
    id_annotation => $annotations[$a_index]->id_annotation,
    id_seq_product => $row->id_seq_product });
}

##########  QC outcomes ##############

my $outcome_type_lib_id = $schema->resultset('QcTypeDict')->search({
  qc_type => 'library'})->next->id_qc_type_dict;
my $outcome_type_seq_id = $schema->resultset('QcTypeDict')->search({
  qc_type => 'sequencing'})->next->id_qc_type_dict;

my %qc_dict = map { $_->outcome, $_->id_qc_outcome_dict}
  $schema->resultset('QcOutcomeDict')->search({})->all();

my $rs_outcome = $schema->resultset('QcOutcome');
my @outcomes = ();
foreach my $row (@rows) {
  my $qc_type = $row->product_layouts->next->sub_product->tags ?
    $outcome_type_lib_id : $outcome_type_seq_id;
  my $o = { id_user => 2,
            id_qc_type_dict => $qc_type,
            created_by => 'demo',
            id_qc_outcome_dict => $qc_dict{'Passed'},
            is_preliminary => 1,
            id_seq_product => $row->id_seq_product
          };
  push @outcomes, $rs_outcome->update_or_create($o);
}

##########  Annotate QC outcomes ############

my $annotation = $rs_annotation->create(
  {id_user => 2, comment => "Passed despite problems", qc_specific => 1});
for my $n ((0,1)) {
  $rs_prod_annotation->update_or_create({
    id_annotation => $annotation->id_annotation,
    id_seq_product => $rows[$n]->id_seq_product
  });
}

1;
