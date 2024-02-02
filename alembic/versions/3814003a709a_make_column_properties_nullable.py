"""Make column properties nullable

Revision ID: 3814003a709a
Revises: 36952df5b8ba
Create Date: 2024-02-02 14:30:20.079955

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "3814003a709a"
down_revision = "36952df5b8ba"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = """
    ALTER TABLE sub_product MODIFY properties JSON DEFAULT NULL
    """
    op.execute(sql)


def downgrade() -> None:
    sql = """
    ALTER TABLE sub_product MODIFY properties JSON NOT NULL
    """
    op.execute(sql)
