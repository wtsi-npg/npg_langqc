use utf8;
package langqc::Schema::Result::SubProductAttr;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::SubProductAttr

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

=head1 TABLE: C<sub_product_attr>

=cut

__PACKAGE__->table("sub_product_attr");

=head1 ACCESSORS

=head2 id_attr

  data_type: 'integer'
  extra: {unsigned => 1}
  is_auto_increment: 1
  is_nullable: 0

=head2 attr_name

  data_type: 'varchar'
  is_nullable: 0
  size: 20

=head2 description

  data_type: 'varchar'
  is_nullable: 0
  size: 255

=cut

__PACKAGE__->add_columns(
  "id_attr",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_auto_increment => 1,
    is_nullable => 0,
  },
  "attr_name",
  { data_type => "varchar", is_nullable => 0, size => 20 },
  "description",
  { data_type => "varchar", is_nullable => 0, size => 255 },
);

=head1 PRIMARY KEY

=over 4

=item * L</id_attr>

=back

=cut

__PACKAGE__->set_primary_key("id_attr");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_subpr_attr>

=over 4

=item * L</attr_name>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_subpr_attr", ["attr_name"]);

=head1 RELATIONS

=head2 sub_product_id_attr_ones

Type: has_many

Related object: L<langqc::Schema::Result::SubProduct>

=cut

__PACKAGE__->has_many(
  "sub_product_id_attr_ones",
  "langqc::Schema::Result::SubProduct",
  { "foreign.id_attr_one" => "self.id_attr" },
  { cascade_copy => 0, cascade_delete => 0 },
);

=head2 sub_product_id_attr_twos

Type: has_many

Related object: L<langqc::Schema::Result::SubProduct>

=cut

__PACKAGE__->has_many(
  "sub_product_id_attr_twos",
  "langqc::Schema::Result::SubProduct",
  { "foreign.id_attr_two" => "self.id_attr" },
  { cascade_copy => 0, cascade_delete => 0 },
);


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-15 13:36:56
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:Spmb7iTiVS2neJA76Ye+UA


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
