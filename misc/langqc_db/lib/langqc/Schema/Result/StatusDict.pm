use utf8;
package langqc::Schema::Result::StatusDict;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::StatusDict

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

=head1 TABLE: C<status_dict>

=cut

__PACKAGE__->table("status_dict");

=head1 ACCESSORS

=head2 id_status_dict

  data_type: 'integer'
  extra: {unsigned => 1}
  is_auto_increment: 1
  is_nullable: 0

=head2 description

  data_type: 'varchar'
  is_nullable: 0
  size: 30

=head2 long_description

  data_type: 'varchar'
  is_nullable: 0
  size: 255

=head2 temporal_index

  data_type: 'integer'
  extra: {unsigned => 1}
  is_nullable: 0

=head2 iscurrent

  data_type: 'tinyint'
  default_value: 1
  is_nullable: 1

=cut

__PACKAGE__->add_columns(
  "id_status_dict",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_auto_increment => 1,
    is_nullable => 0,
  },
  "description",
  { data_type => "varchar", is_nullable => 0, size => 30 },
  "long_description",
  { data_type => "varchar", is_nullable => 0, size => 255 },
  "temporal_index",
  { data_type => "integer", extra => { unsigned => 1 }, is_nullable => 0 },
  "iscurrent",
  { data_type => "tinyint", default_value => 1, is_nullable => 1 },
);

=head1 PRIMARY KEY

=over 4

=item * L</id_status_dict>

=back

=cut

__PACKAGE__->set_primary_key("id_status_dict");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_status_dict_desc>

=over 4

=item * L</description>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_status_dict_desc", ["description"]);

=head1 RELATIONS

=head2 statuses

Type: has_many

Related object: L<langqc::Schema::Result::Status>

=cut

__PACKAGE__->has_many(
  "statuses",
  "langqc::Schema::Result::Status",
  { "foreign.id_status_dict" => "self.id_status_dict" },
  { cascade_copy => 0, cascade_delete => 0 },
);


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-15 13:36:56
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:t1tyK6JMq+u2rB8LyRvWGw


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
