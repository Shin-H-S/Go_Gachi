"""add role check constraint to profiles

Revision ID: 4f7172c4d0c4
Revises: 0ca935824641
Create Date: 2026-06-01 05:11:47.973716

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4f7172c4d0c4'
down_revision: str | Sequence[str] | None = '0ca935824641'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """profiles.role에 'user'/'admin'만 허용하는 CHECK 제약을 추가한다."""
    op.create_check_constraint(
        "ck_profiles_role",
        "profiles",
        "role IN ('user', 'admin')",
    )


def downgrade() -> None:
    """role CHECK 제약을 제거한다."""
    op.drop_constraint("ck_profiles_role", "profiles", type_="check")
