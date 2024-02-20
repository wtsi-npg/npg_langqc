"""drop_json_properties_column

Revision ID: 2.0.0
Revises: 3814003a709a
Create Date: 2024-02-20 10:51:40.326882

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2.0.0"
down_revision = "3814003a709a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = """
    ALTER TABLE sub_product DROP COLUMN properties
    """
    op.execute(sql)


def downgrade() -> None:
    sql = """
    ALTER TABLE sub_product ADD COLUMN properties JSON DEFAULT NULL AFTER value_attr_three
    """
    op.execute(sql)
    pass
