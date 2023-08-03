"""Add ability to record plate number

Revision ID: 36952df5b8ba
Revises: dd60c67ad3e5
Create Date: 2023-08-03 13:32:06.820978

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "36952df5b8ba"
down_revision = "dd60c67ad3e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = """
    INSERT INTO sub_product_attr (`attr_name`, `description`)
    VALUES ('plate_number', 'An optional PacBio plate number')
    """
    op.execute(sql)

    sql = """
    ALTER TABLE sub_product
      ADD COLUMN `id_attr_three` INT DEFAULT NULL AFTER `value_attr_two`,
      ADD COLUMN `value_attr_three` VARCHAR(20) DEFAULT NULL AFTER `id_attr_three`,
      ADD KEY `ix_sub_product_id_attr_three` (`id_attr_three`),
      ADD KEY `ix_sub_product_value_attr_three` (`value_attr_three`),
      ADD CONSTRAINT `fk_subproduct_attr3` FOREIGN KEY (`id_attr_three`)
          REFERENCES `sub_product_attr` (`id_attr`);
    """
    op.execute(sql)


def downgrade() -> None:
    sql = """
    ALTER TABLE sub_product
        DROP KEY `ix_sub_product_id_attr_three`,
        DROP KEY `ix_sub_product_value_attr_three`,
        DROP CONSTRAINT `fk_subproduct_attr3`,
        DROP COLUMN `value_attr_three`,
        DROP COLUMN `id_attr_three`;
    """
    op.execute(sql)

    sql = """
    DELETE FROM sub_product_attr WHERE attr_name='plate_number';
    """
    op.execute(sql)
