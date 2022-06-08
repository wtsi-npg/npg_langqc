use utf8;
package langqc::Schema::Result::Annotation;

# Created by DBIx::Class::Schema::Loader
# DO NOT MODIFY THE FIRST PART OF THIS FILE

=head1 NAME

langqc::Schema::Result::Annotation

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

=head1 TABLE: C<annotation>

=cut

__PACKAGE__->table("annotation");

=head1 ACCESSORS

=head2 id_annotation

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

=head2 comment

  data_type: 'text'
  is_nullable: 0

=cut

__PACKAGE__->add_columns(
  "id_annotation",
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
  "comment",
  { data_type => "text", is_nullable => 0 },
);

=head1 PRIMARY KEY

=over 4

=item * L</id_annotation>

=back

=cut

__PACKAGE__->set_primary_key("id_annotation");

=head1 RELATIONS

=head2 product_annotations

Type: has_many

Related object: L<langqc::Schema::Result::ProductAnnotation>

=cut

__PACKAGE__->has_many(
  "product_annotations",
  "langqc::Schema::Result::ProductAnnotation",
  { "foreign.id_annotation" => "self.id_annotation" },
  { cascade_copy => 0, cascade_delete => 0 },
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
# DO NOT MODIFY THIS OR ANYTHING ABOVE! md5sum:6mmhWvBC0W2Y50xWtNSEfA


# You can replace this text with custom code or comments, and it will be preserved on regeneration
__PACKAGE__->meta->make_immutable;
1;
