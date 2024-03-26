"""extend_qc_state_dict

Revision ID: 2.1.0
Revises: 2.0.0
Create Date: 2024-03-19 12:31:26.359652

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2.1.0"
down_revision = "2.0.0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("INSERT INTO qc_state_dict VALUES ('On hold external', NULL)")


def downgrade() -> None:
    op.execute("DELETE FROM qc_state_dict WHERE state='On hold external'")
