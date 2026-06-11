"""add generation parent id

Revision ID: e1a2b3c4d5f6
Revises: b7a3c9d2e8f1
Create Date: 2026-06-09 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5f6"
down_revision: str | Sequence[str] | None = "b7a3c9d2e8f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("generations", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_generations_parent_id"), "generations", ["parent_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_generations_parent_id_generations"),
        "generations",
        "generations",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("fk_generations_parent_id_generations"),
        "generations",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_generations_parent_id"), table_name="generations")
    op.drop_column("generations", "parent_id")
