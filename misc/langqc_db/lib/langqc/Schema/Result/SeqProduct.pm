use utf8;
package langqc::Schema::Result::SeqProduct;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::SeqProduct

=cut

use strict;
use warnings;

use Moose;
use MooseX::NonMoose;
use MooseX::MarkAsMethods autoclean => 1;
extends 'DBIx::Class::Core';

=head1 COMPONENTS LOADED

=over 4

=item * L<DBIx::Class::InflateColumn::DateTime>

=back

=cut

__PACKAGE__->load_components("InflateColumn::DateTime");

=head1 TABLE: C<seq_product>

=cut

__PACKAGE__->table("seq_product");

=head1 ACCESSORS

=head2 id_seq_product

  data_type: 'bigint'
  extra: {unsigned => 1}
  is_auto_increment: 1
  is_nullable: 0

=head2 id_product

  data_type: 'char'
  is_nullable: 0
  size: 64

=head2 id_product_category_dict

  data_type: 'integer'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=cut

__PACKAGE__->add_columns(
  "id_seq_product",
  {
    data_type => "bigint",
    extra => { unsigned => 1 },
    is_auto_increment => 1,
    is_nullable => 0,
  },
  "id_product",
  { data_type => "char", is_nullable => 0, size => 64 },
  "id_product_category_dict",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
);

=head1 PRIMARY KEY

=over 4

=item * L</id_seq_product>

=back

=cut

__PACKAGE__->set_primary_key("id_seq_product");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_product>

=over 4

=item * L</id_product>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_product", ["id_product"]);

=head1 RELATIONS

=head2 product_annotations

Type: has_many

Related object: L<langqc::Schema::Result::ProductAnnotation>

=cut

__PACKAGE__->has_many(
  "product_annotations",
  "langqc::Schema::Result::ProductAnnotation",
  { "foreign.id_seq_product" => "self.id_seq_product" },
  { cascade_copy => 0, cascade_delete => 0 },
);

=head2 product_category_dict

Type: belongs_to

Related object: L<langqc::Schema::Result::ProductCategoryDict>

=cut

__PACKAGE__->belongs_to(
  "product_category_dict",
  "langqc::Schema::Result::ProductCategoryDict",
  { id_product_category_dict => "id_product_category_dict" },
  { is_deferrable => 1, on_delete => "NO ACTION", on_update => "NO ACTION" },
);

=head2 product_compositions

Type: has_many

Related object: L<langqc::Schema::Result::ProductComposition>

=cut

__PACKAGE__->has_many(
  "product_compositions",
  "langqc::Schema::Result::ProductComposition",
  { "foreign.id_seq_product" => "self.id_seq_product" },
  { cascade_copy => 0, cascade_delete => 0 },
);

=head2 qc_outcome_hists

Type: has_many

Related object: L<langqc::Schema::Result::QcOutcomeHist>

=cut

__PACKAGE__->has_many(
  "qc_outcome_hists",
  "langqc::Schema::Result::QcOutcomeHist",
  { "foreign.id_seq_product" => "self.id_seq_product" },
  { cascade_copy => 0, cascade_delete => 0 },
);

=head2 qc_outcomes

Type: has_many

Related object: L<langqc::Schema::Result::QcOutcome>

=cut

__PACKAGE__->has_many(
  "qc_outcomes",
  "langqc::Schema::Result::QcOutcome",
  { "foreign.id_seq_product" => "self.id_seq_product" },
  { cascade_copy => 0, cascade_delete => 0 },
);


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-06 10:18:13
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:/qWwe5hQhxlJjGlpgqrIaQ


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
