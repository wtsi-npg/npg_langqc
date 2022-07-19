use utf8;
package langqc::Schema::Result::QcState;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::QcState

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

=head1 TABLE: C<qc_state>

=cut

__PACKAGE__->table("qc_state");

=head1 ACCESSORS

=head2 id_qc_state

  data_type: 'bigint'
  extra: {unsigned => 1}
  is_auto_increment: 1
  is_nullable: 0

=head2 id_seq_product

  data_type: 'bigint'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=head2 id_user

  data_type: 'integer'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=head2 id_qc_state_dict

  data_type: 'integer'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=head2 id_qc_type

  data_type: 'integer'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=head2 is_preliminary

  data_type: 'tinyint'
  default_value: 1
  is_nullable: 1

=head2 created_by

  data_type: 'varchar'
  is_nullable: 0
  size: 20

=head2 date_created

  data_type: 'datetime'
  datetime_undef_if_invalid: 1
  default_value: 'CURRENT_TIMESTAMP'
  is_nullable: 1

Datetime this record was created

=head2 date_updated

  data_type: 'datetime'
  datetime_undef_if_invalid: 1
  default_value: 'CURRENT_TIMESTAMP'
  is_nullable: 1

Datetime this record was created or changed

=cut

__PACKAGE__->add_columns(
  "id_qc_state",
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
  "id_user",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
  "id_qc_state_dict",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
  "id_qc_type",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
  "is_preliminary",
  { data_type => "tinyint", default_value => 1, is_nullable => 1 },
  "created_by",
  { data_type => "varchar", is_nullable => 0, size => 20 },
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
);

=head1 PRIMARY KEY

=over 4

=item * L</id_qc_state>

=back

=cut

__PACKAGE__->set_primary_key("id_qc_state");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_qc_state>

=over 4

=item * L</id_seq_product>

=item * L</id_qc_type>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_qc_state", ["id_seq_product", "id_qc_type"]);

=head1 RELATIONS

=head2 qc_state_dict

Type: belongs_to

Related object: L<langqc::Schema::Result::QcStateDict>

=cut

__PACKAGE__->belongs_to(
  "qc_state_dict",
  "langqc::Schema::Result::QcStateDict",
  { id_qc_state_dict => "id_qc_state_dict" },
  { is_deferrable => 1, on_delete => "NO ACTION", on_update => "NO ACTION" },
);

=head2 qc_type

Type: belongs_to

Related object: L<langqc::Schema::Result::QcType>

=cut

__PACKAGE__->belongs_to(
  "qc_type",
  "langqc::Schema::Result::QcType",
  { id_qc_type => "id_qc_type" },
  { is_deferrable => 1, on_delete => "NO ACTION", on_update => "NO ACTION" },
);

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

=head2 user

Type: belongs_to

Related object: L<langqc::Schema::Result::User>

=cut

__PACKAGE__->belongs_to(
  "user",
  "langqc::Schema::Result::User",
  { id_user => "id_user" },
  { is_deferrable => 1, on_delete => "NO ACTION", on_update => "NO ACTION" },
);


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-24 11:32:13
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:T4FSs3jGqF6WWRv0ezwAKA


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
