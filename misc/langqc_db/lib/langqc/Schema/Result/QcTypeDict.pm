use utf8;
package langqc::Schema::Result::QcTypeDict;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::QcTypeDict

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

=head1 TABLE: C<qc_type_dict>

=cut

__PACKAGE__->table("qc_type_dict");

=head1 ACCESSORS

=head2 id_qc_type_dict

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
  "id_qc_type_dict",
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

=item * L</id_qc_type_dict>

=back

=cut

__PACKAGE__->set_primary_key("id_qc_type_dict");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_qc_type_dict>

=over 4

=item * L</qc_type>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_qc_type_dict", ["qc_type"]);

=head1 RELATIONS

=head2 qc_outcome_hists

Type: has_many

Related object: L<langqc::Schema::Result::QcOutcomeHist>

=cut

__PACKAGE__->has_many(
  "qc_outcome_hists",
  "langqc::Schema::Result::QcOutcomeHist",
  { "foreign.id_qc_type_dict" => "self.id_qc_type_dict" },
  { cascade_copy => 0, cascade_delete => 0 },
);

=head2 qc_outcomes

Type: has_many

Related object: L<langqc::Schema::Result::QcOutcome>

=cut

__PACKAGE__->has_many(
  "qc_outcomes",
  "langqc::Schema::Result::QcOutcome",
  { "foreign.id_qc_type_dict" => "self.id_qc_type_dict" },
  { cascade_copy => 0, cascade_delete => 0 },
);


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-15 13:36:56
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:PRN6LuM2yquYIvmAb191qw


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
