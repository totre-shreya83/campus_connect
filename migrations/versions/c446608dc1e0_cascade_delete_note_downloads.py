"""Cascade delete note downloads

Revision ID: c446608dc1e0
Revises: 6cb67f2a5627
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c446608dc1e0"
down_revision = "6cb67f2a5627"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        ALTER TABLE downloads
        DROP FOREIGN KEY downloads_ibfk_1
        """
    )

    op.execute(
        """
        ALTER TABLE downloads
        ADD CONSTRAINT downloads_ibfk_1
        FOREIGN KEY (note_id)
        REFERENCES notes (id)
        ON DELETE CASCADE
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE downloads
        DROP FOREIGN KEY downloads_ibfk_1
        """
    )

    op.execute(
        """
        ALTER TABLE downloads
        ADD CONSTRAINT downloads_ibfk_1
        FOREIGN KEY (note_id)
        REFERENCES notes (id)
        """
    )