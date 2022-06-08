use utf8;
package langqc::Schema::Result::SeqPlatformDict;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::SeqPlatformDict

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

=head1 TABLE: C<seq_platform_dict>

=cut

__PACKAGE__->table("seq_platform_dict");

=head1 ACCESSORS

=head2 id_seq_platform_dict

  data_type: 'integer'
  extra: {unsigned => 1}
  is_auto_increment: 1
  is_nullable: 0

=head2 name

  data_type: 'varchar'
  is_nullable: 0
  size: 10

=head2 description

  data_type: 'varchar'
  is_nullable: 0
  size: 256

=head2 iscurrent

  data_type: 'tinyint'
  default_value: 1
  is_nullable: 0

=cut

__PACKAGE__->add_columns(
  "id_seq_platform_dict",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_auto_increment => 1,
    is_nullable => 0,
  },
  "name",
  { data_type => "varchar", is_nullable => 0, size => 10 },
  "description",
  { data_type => "varchar", is_nullable => 0, size => 256 },
  "iscurrent",
  { data_type => "tinyint", default_value => 1, is_nullable => 0 },
);

=head1 PRIMARY KEY

=over 4

=item * L</id_seq_platform_dict>

=back

=cut

__PACKAGE__->set_primary_key("id_seq_platform_dict");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_seq_platform_name>

=over 4

=item * L</name>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_seq_platform_name", ["name"]);

=head1 RELATIONS

=head2 seq_products

Type: has_many

Related object: L<langqc::Schema::Result::SeqProduct>

=cut

__PACKAGE__->has_many(
  "seq_products",
  "langqc::Schema::Result::SeqProduct",
  { "foreign.id_seq_platform_dict" => "self.id_seq_platform_dict" },
  { cascade_copy => 0, cascade_delete => 0 },
);


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-09 17:51:01
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:Pb2s/xehUFhMVUFVB+/qOg


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
