"""Extend username column

Revision ID: 50eb2dc8f2cd
Revises: 67fddcef9a89
Create Date: 2022-08-11 14:31:31.087803

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "50eb2dc8f2cd"
down_revision = "67fddcef9a89"
branch_labels = None
depends_on = None


def upgrade() -> None:

    sql = """
    ALTER TABLE `user`
    MODIFY `username` VARCHAR(255) NOT NULL
    """
    op.execute(sql)


def downgrade() -> None:

    sql = """
    ALTER TABLE `user`
    MODIFY `username` VARCHAR(12) NOT NULL
    """
    op.execute(sql)
