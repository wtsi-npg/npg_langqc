use utf8;
package langqc::Schema::Result::VendorCommunication;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::VendorCommunication

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

=head1 TABLE: C<vendor_communication>

=cut

__PACKAGE__->table("vendor_communication");

=head1 ACCESSORS

=head2 id_vendor_communication

  data_type: 'bigint'
  extra: {unsigned => 1}
  is_auto_increment: 1
  is_nullable: 0

=head2 id_user

  data_type: 'integer'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

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

=head2 id_seq_product

  data_type: 'bigint'
  extra: {unsigned => 1}
  is_foreign_key: 1
  is_nullable: 0

=head2 query

  data_type: 'text'
  is_nullable: 0

=head2 vendor_tracking_id

  data_type: 'varchar'
  is_nullable: 1
  size: 256

=head2 vendor_response

  data_type: 'text'
  is_nullable: 1

=head2 vendor_refund

  data_type: 'varchar'
  is_nullable: 1
  size: 256

=cut

__PACKAGE__->add_columns(
  "id_vendor_communication",
  {
    data_type => "bigint",
    extra => { unsigned => 1 },
    is_auto_increment => 1,
    is_nullable => 0,
  },
  "id_user",
  {
    data_type => "integer",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
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
  "id_seq_product",
  {
    data_type => "bigint",
    extra => { unsigned => 1 },
    is_foreign_key => 1,
    is_nullable => 0,
  },
  "query",
  { data_type => "text", is_nullable => 0 },
  "vendor_tracking_id",
  { data_type => "varchar", is_nullable => 1, size => 256 },
  "vendor_response",
  { data_type => "text", is_nullable => 1 },
  "vendor_refund",
  { data_type => "varchar", is_nullable => 1, size => 256 },
);

=head1 PRIMARY KEY

=over 4

=item * L</id_vendor_communication>

=back

=cut

__PACKAGE__->set_primary_key("id_vendor_communication");

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


# Created by DBIx::Class::Schema::Loader v0.07049 @ 2022-06-10 12:17:34
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:fORyYht9MLkpKWshmf3HaQ


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
