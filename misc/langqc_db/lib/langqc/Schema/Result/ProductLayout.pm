use utf8;
package langqc::Schema::Result::ProductLayout;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::ProductLayout

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

=head1 TABLE: C<product_layout>

=cut

__PACKAGE__->table("product_layout");

=head1 ACCESSORS

=head2 id_product_layout

  data_type: 'bigint'
  extra: {unsigned => 1}
  is_auto_increment: 1
  is_nullable: 0

=head2 id_seq_product

  data_type: 'bigint'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=head2 id_sub_product

  data_type: 'bigint'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=cut

__PACKAGE__->add_columns(
  "id_product_layout",
  {
    data_type => "bigint",
    extra => { unsigned => 1 },
    is_auto_increment => 1,
    is_nullable => 0,
  },
  "id_seq_product",
  {
    data_type => "bigint",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
  "id_sub_product",
  {
    data_type => "bigint",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
);

=head1 PRIMARY KEY

=over 4

=item * L</id_product_layout>

=back

=cut

__PACKAGE__->set_primary_key("id_product_layout");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_product_layout>

=over 4

=item * L</id_seq_product>

=item * L</id_sub_product>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_product_layout", ["id_seq_product", "id_sub_product"]);

=head1 RELATIONS

=head2 seq_product

Type: belongs_to

Related object: L<langqc::Schema::Result::SeqProduct>

=cut

__PACKAGE__->belongs_to(
  "seq_product",
  "langqc::Schema::Result::SeqProduct",
  { id_seq_product => "id_seq_product" },
  { is_deferrable => 1, on_delete => "NO ACTION", on_update => "NO ACTION" },
);

=head2 sub_product

Type: belongs_to

Related object: L<langqc::Schema::Result::SubProduct>

=cut

__PACKAGE__->belongs_to(
  "sub_product",
  "langqc::Schema::Result::SubProduct",
  { id_sub_product => "id_sub_product" },
  { is_deferrable => 1, on_delete => "NO ACTION", on_update => "NO ACTION" },
);


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-09 17:38:31
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:6VEqrCWHNaX2D8DTO10ZRQ


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
