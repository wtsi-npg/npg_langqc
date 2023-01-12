"""index_qc_state_date_column

Revision ID: 0a3a2726e378
Revises: dd60c67ad3e5
Create Date: 2023-01-12 10:42:54.463279

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0a3a2726e378"
down_revision = "dd60c67ad3e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create search indexes to speed-up data retrieval and sorting.
    Note the descendant order of the index on the `qc_state.date_updated`
    column. This index is suboptimal for sorting in ascending order, a
    separate index can be created to support that.
    """

    op.execute(
        """
    ALTER TABLE `qc_state`
    ADD INDEX `qc_state_date_updated_desc_index` (`date_updated` DESC),
    ADD INDEX `qc_state_is_prelim_index` (`is_preliminary`)
    """
    )
    op.execute(
        """
    ALTER TABLE `qc_state_dict`
    ADD INDEX `qc_state_outcome_index` (`outcome`)
    """
    )


def downgrade() -> None:
    """
    Drop all indexes that are created by this migration.
    """

    op.execute(
        """
    ALTER TABLE `qc_state`
    DROP INDEX `qc_state_date_updated_desc_index`,
    DROP INDEX `qc_state_is_prelim_index`
    """
    )
    op.execute(
        """
    ALTER TABLE `qc_state_dict`
    DROP INDEX `qc_state_outcome_index`"""
    )
