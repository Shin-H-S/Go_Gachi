"""add generation metadata

Revision ID: dff5cf1cfe4f
Revises: b7a3c9d2e8f1
Create Date: 2026-06-09 13:05:20.438641

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dff5cf1cfe4f"
down_revision: str | Sequence[str] | None = "b7a3c9d2e8f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("generations", sa.Column("user_copy", sa.Text(), nullable=True))
    op.add_column(
        "generations",
        sa.Column("has_logo", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("generations", sa.Column("logo_position", sa.String(length=50), nullable=True))
    op.add_column("generations", sa.Column("logo_image_hash", sa.String(length=64), nullable=True))
    op.add_column(
        "generations",
        sa.Column("logo_storage_key", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("generations", "logo_storage_key")
    op.drop_column("generations", "logo_image_hash")
    op.drop_column("generations", "logo_position")
    op.drop_column("generations", "has_logo")
    op.drop_column("generations", "user_copy")
