"""fix typo in dict data

Revision ID: 23c7eda792e2
Revises: 0a3a2726e378
Create Date: 2023-03-02 15:09:31.175328

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "23c7eda792e2"
down_revision = "0a3a2726e378"
branch_labels = None
depends_on = None


def upgrade() -> None:

    sql = """
    UPDATE qc_type
    SET description='Sequencing/instrument evaluation' WHERE qc_type='sequencing'
    """
    op.execute(sql)


def downgrade() -> None:

    sql = """
    UPDATE qc_type
    SET description='Sequencing/instrument evaliation' WHERE qc_type='sequencing'
    """
    op.execute(sql)
