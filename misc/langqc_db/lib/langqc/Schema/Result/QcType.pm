use utf8;
package langqc::Schema::Result::QcType;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::QcType

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

=head1 TABLE: C<qc_type>

=cut

__PACKAGE__->table("qc_type");

=head1 ACCESSORS

=head2 id_qc_type

  data_type: 'integer'
  extra: {unsigned => 1}
  is_auto_increment: 1
  is_nullable: 0

=head2 qc_type

  data_type: 'varchar'
  is_nullable: 0
  size: 10

=head2 description

  data_type: 'varchar'
  is_nullable: 0
  size: 255

=cut

__PACKAGE__->add_columns(
  "id_qc_type",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_auto_increment => 1,
    is_nullable => 0,
  },
  "qc_type",
  { data_type => "varchar", is_nullable => 0, size => 10 },
  "description",
  { data_type => "varchar", is_nullable => 0, size => 255 },
);

=head1 PRIMARY KEY

=over 4

=item * L</id_qc_type>

=back

=cut

__PACKAGE__->set_primary_key("id_qc_type");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_qc_type>

=over 4

=item * L</qc_type>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_qc_type", ["qc_type"]);

=head1 RELATIONS

=head2 qc_state_hists

Type: has_many

Related object: L<langqc::Schema::Result::QcStateHist>

=cut

__PACKAGE__->has_many(
  "qc_state_hists",
  "langqc::Schema::Result::QcStateHist",
  { "foreign.id_qc_type" => "self.id_qc_type" },
  { cascade_copy => 0, cascade_delete => 0 },
);

=head2 qc_states

Type: has_many

Related object: L<langqc::Schema::Result::QcState>

=cut

__PACKAGE__->has_many(
  "qc_states",
  "langqc::Schema::Result::QcState",
  { "foreign.id_qc_type" => "self.id_qc_type" },
  { cascade_copy => 0, cascade_delete => 0 },
);


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-24 11:32:13
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:T47drKNH2SsmKj6Lgg27fA


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
