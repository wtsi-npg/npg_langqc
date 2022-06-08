use utf8;
package langqc::Schema::Result::User;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::User

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

=head1 TABLE: C<user>

=cut

__PACKAGE__->table("user");

=head1 ACCESSORS

=head2 id_user

  data_type: 'integer'
  extra: {unsigned => 1}
  is_auto_increment: 1
  is_nullable: 0

=head2 username

  data_type: 'varchar'
  is_nullable: 0
  size: 12

=head2 date_created

  data_type: 'datetime'
  datetime_undef_if_invalid: 1
  default_value: 'CURRENT_TIMESTAMP'
  is_nullable: 1

Datetime the user record was created

=head2 date_updated

  data_type: 'datetime'
  datetime_undef_if_invalid: 1
  default_value: 'CURRENT_TIMESTAMP'
  is_nullable: 1

Datetime the user record was created or changed

=head2 iscurrent

  data_type: 'tinyint'
  default_value: 1
  is_nullable: 0

=cut

__PACKAGE__->add_columns(
  "id_user",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_auto_increment => 1,
    is_nullable => 0,
  },
  "username",
  { data_type => "varchar", is_nullable => 0, size => 12 },
  "date_created",
  {
    data_type => "datetime",
    datetime_undef_if_invalid => 1,
    default_value => "CURRENT_TIMESTAMP",
    is_nullable => 1,
  },
  "date_updated",
  {
    data_type => "datetime",
    datetime_undef_if_invalid => 1,
    default_value => "CURRENT_TIMESTAMP",
    is_nullable => 1,
  },
  "iscurrent",
  { data_type => "tinyint", default_value => 1, is_nullable => 0 },
);

=head1 PRIMARY KEY

=over 4

=item * L</id_user>

=back

=cut

__PACKAGE__->set_primary_key("id_user");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_user>

=over 4

=item * L</username>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_user", ["username"]);

=head1 RELATIONS

=head2 annotations

Type: has_many

Related object: L<langqc::Schema::Result::Annotation>

=cut

__PACKAGE__->has_many(
  "annotations",
  "langqc::Schema::Result::Annotation",
  { "foreign.id_user" => "self.id_user" },
  { cascade_copy => 0, cascade_delete => 0 },
);

=head2 qc_outcome_hists

Type: has_many

Related object: L<langqc::Schema::Result::QcOutcomeHist>

=cut

__PACKAGE__->has_many(
  "qc_outcome_hists",
  "langqc::Schema::Result::QcOutcomeHist",
  { "foreign.id_user" => "self.id_user" },
  { cascade_copy => 0, cascade_delete => 0 },
);

=head2 qc_outcomes

Type: has_many

Related object: L<langqc::Schema::Result::QcOutcome>

=cut

__PACKAGE__->has_many(
  "qc_outcomes",
  "langqc::Schema::Result::QcOutcome",
  { "foreign.id_user" => "self.id_user" },
  { cascade_copy => 0, cascade_delete => 0 },
);


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-06 10:18:13
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:nlhMXZSDeSGw4SEZQkwIsg


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
