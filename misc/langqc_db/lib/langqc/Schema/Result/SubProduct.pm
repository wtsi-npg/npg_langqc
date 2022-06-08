use utf8;
package langqc::Schema::Result::SubProduct;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::SubProduct

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

=head1 TABLE: C<sub_product>

=cut

__PACKAGE__->table("sub_product");

=head1 ACCESSORS

=head2 id_sub_product

  data_type: 'bigint'
  extra: {unsigned => 1}
  is_auto_increment: 1
  is_nullable: 0

=head2 id_attr_one

  data_type: 'integer'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=head2 value_attr_one

  data_type: 'varchar'
  is_nullable: 0
  size: 20

=head2 id_attr_two

  data_type: 'integer'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=head2 value_attr_two

  data_type: 'varchar'
  is_nullable: 0
  size: 20

=head2 tag_one

  data_type: 'varchar'
  is_nullable: 1
  size: 20

=head2 tag_two

  data_type: 'varchar'
  is_nullable: 1
  size: 20

=head2 id_seq_platform_dict

  data_type: 'integer'
  extra: {unsigned => 1}
  is_nullable: 0

=head2 description

  data_type: 'json'
  is_nullable: 0

=head2 digest

  data_type: 'char'
  is_nullable: 0
  size: 64

=cut

__PACKAGE__->add_columns(
  "id_sub_product",
  {
    data_type => "bigint",
    extra => { unsigned => 1 },
    is_auto_increment => 1,
    is_nullable => 0,
  },
  "id_attr_one",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
  "value_attr_one",
  { data_type => "varchar", is_nullable => 0, size => 20 },
  "id_attr_two",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
  "value_attr_two",
  { data_type => "varchar", is_nullable => 0, size => 20 },
  "tag_one",
  { data_type => "varchar", is_nullable => 1, size => 20 },
  "tag_two",
  { data_type => "varchar", is_nullable => 1, size => 20 },
  "id_seq_platform_dict",
  { data_type => "integer", extra => { unsigned => 1 }, is_nullable => 0 },
  "description",
  { data_type => "json", is_nullable => 0 },
  "digest",
  { data_type => "char", is_nullable => 0, size => 64 },
);

=head1 PRIMARY KEY

=over 4

=item * L</id_sub_product>

=back

=cut

__PACKAGE__->set_primary_key("id_sub_product");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_sub_product_digest>

=over 4

=item * L</digest>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_sub_product_digest", ["digest"]);

=head1 RELATIONS

=head2 attr_one

Type: belongs_to

Related object: L<langqc::Schema::Result::SubProductAttr>

=cut

__PACKAGE__->belongs_to(
  "attr_one",
  "langqc::Schema::Result::SubProductAttr",
  { id_attr => "id_attr_one" },
  { is_deferrable => 1, on_delete => "NO ACTION", on_update => "NO ACTION" },
);

=head2 attr_two

Type: belongs_to

Related object: L<langqc::Schema::Result::SubProductAttr>

=cut

__PACKAGE__->belongs_to(
  "attr_two",
  "langqc::Schema::Result::SubProductAttr",
  { id_attr => "id_attr_two" },
  { is_deferrable => 1, on_delete => "NO ACTION", on_update => "NO ACTION" },
);

=head2 product_compositions

Type: has_many

Related object: L<langqc::Schema::Result::ProductComposition>

=cut

__PACKAGE__->has_many(
  "product_compositions",
  "langqc::Schema::Result::ProductComposition",
  { "foreign.id_sub_product" => "self.id_sub_product" },
  { cascade_copy => 0, cascade_delete => 0 },
);


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-06 10:18:13
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:3RKL2Xko400NlbXolXCpsw


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
