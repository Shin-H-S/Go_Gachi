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
    op.drop_index(op.f("ix_api_usage_model"), table_name="api_usage")
    op.alter_column(
        "api_usage",
        "estimated_cost",
        new_column_name="cost_usd",
        existing_type=sa.Float(),
        existing_nullable=False,
    )
    op.add_column("api_usage", sa.Column("image_model", sa.String(length=120), nullable=True))
    op.add_column("api_usage", sa.Column("text_model", sa.String(length=120), nullable=True))
    op.add_column(
        "api_usage",
        sa.Column("image_cost_usd", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "api_usage",
        sa.Column("text_cost_usd", sa.Float(), nullable=False, server_default="0"),
    )
    op.execute("UPDATE api_usage SET image_model = model, image_cost_usd = cost_usd")
    op.drop_column("api_usage", "operation")
    op.drop_column("api_usage", "model")
    op.create_index(op.f("ix_api_usage_image_model"), "api_usage", ["image_model"], unique=False)
    op.create_index(op.f("ix_api_usage_text_model"), "api_usage", ["text_model"], unique=False)
    op.add_column(
        "generations",
        sa.Column("text_model", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("generations", "text_model")
    op.drop_index(op.f("ix_api_usage_text_model"), table_name="api_usage")
    op.drop_index(op.f("ix_api_usage_image_model"), table_name="api_usage")
    op.add_column(
        "api_usage",
        sa.Column("model", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "api_usage",
        sa.Column("operation", sa.String(length=80), nullable=False, server_default="image_edit"),
    )
    op.execute("UPDATE api_usage SET model = COALESCE(image_model, text_model, 'unknown')")
    op.alter_column("api_usage", "model", nullable=False)
    op.drop_column("api_usage", "text_cost_usd")
    op.drop_column("api_usage", "image_cost_usd")
    op.drop_column("api_usage", "text_model")
    op.drop_column("api_usage", "image_model")
    op.alter_column(
        "api_usage",
        "cost_usd",
        new_column_name="estimated_cost",
        existing_type=sa.Float(),
        existing_nullable=False,
    )
    op.create_index(op.f("ix_api_usage_model"), "api_usage", ["model"], unique=False)
