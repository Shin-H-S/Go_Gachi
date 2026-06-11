"""rename usage cost and add text model

Revision ID: c2f4a8b1d9e3
Revises: dff5cf1cfe4f
Create Date: 2026-06-11

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2f4a8b1d9e3"
down_revision: str | Sequence[str] | None = "dff5cf1cfe4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "api_usage",
        "estimated_cost",
        new_column_name="cost_usd",
        existing_type=sa.Float(),
        existing_nullable=False,
    )
    op.add_column(
        "generations",
        sa.Column("text_model", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("generations", "text_model")
    op.alter_column(
        "api_usage",
        "cost_usd",
        new_column_name="estimated_cost",
        existing_type=sa.Float(),
        existing_nullable=False,
    )
