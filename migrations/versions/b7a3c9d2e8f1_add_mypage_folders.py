"""add mypage folders

Revision ID: b7a3c9d2e8f1
Revises: 4f7172c4d0c4
Create Date: 2026-06-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7a3c9d2e8f1"
down_revision: str | Sequence[str] | None = "4f7172c4d0c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "folders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_folders_user_id_name"),
    )
    op.create_index(op.f("ix_folders_user_id"), "folders", ["user_id"], unique=False)
    op.add_column("generations", sa.Column("folder_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_generations_folder_id"), "generations", ["folder_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_generations_folder_id_folders"),
        "generations",
        "folders",
        ["folder_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("fk_generations_folder_id_folders"), "generations", type_="foreignkey")
    op.drop_index(op.f("ix_generations_folder_id"), table_name="generations")
    op.drop_column("generations", "folder_id")
    op.drop_index(op.f("ix_folders_user_id"), table_name="folders")
    op.drop_table("folders")
