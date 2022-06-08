use utf8;
package langqc::Schema::Result::QcOutcome;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::QcOutcome

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

=head1 TABLE: C<qc_outcome>

=cut

__PACKAGE__->table("qc_outcome");

=head1 ACCESSORS

=head2 id_qc_outcome

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

=head2 id_qc_outcome_dict

  data_type: 'integer'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=head2 id_qc_type_dict

  data_type: 'integer'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

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
  "id_qc_outcome",
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
  "id_qc_outcome_dict",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
  "id_qc_type_dict",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
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

=item * L</id_qc_outcome>

=back

=cut

__PACKAGE__->set_primary_key("id_qc_outcome");

=head1 UNIQUE CONSTRAINTS

=head2 C<unique_qc_outcome>

=over 4

=item * L</id_seq_product>

=item * L</id_qc_type_dict>

=back

=cut

__PACKAGE__->add_unique_constraint("unique_qc_outcome", ["id_seq_product", "id_qc_type_dict"]);

=head1 RELATIONS

=head2 product_annotations

Type: has_many

Related object: L<langqc::Schema::Result::ProductAnnotation>

=cut

__PACKAGE__->has_many(
  "product_annotations",
  "langqc::Schema::Result::ProductAnnotation",
  { "foreign.id_qc_outcome" => "self.id_qc_outcome" },
  { cascade_copy => 0, cascade_delete => 0 },
);

=head2 qc_outcome_dict

Type: belongs_to

Related object: L<langqc::Schema::Result::QcOutcomeDict>

=cut

__PACKAGE__->belongs_to(
  "qc_outcome_dict",
  "langqc::Schema::Result::QcOutcomeDict",
  { id_qc_outcome_dict => "id_qc_outcome_dict" },
  { is_deferrable => 1, on_delete => "NO ACTION", on_update => "NO ACTION" },
);

=head2 qc_type_dict

Type: belongs_to

Related object: L<langqc::Schema::Result::QcTypeDict>

=cut

__PACKAGE__->belongs_to(
  "qc_type_dict",
  "langqc::Schema::Result::QcTypeDict",
  { id_qc_type_dict => "id_qc_type_dict" },
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


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-06 10:18:13
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:8UUvgQwYeIWVuUwjtlLbMQ


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
