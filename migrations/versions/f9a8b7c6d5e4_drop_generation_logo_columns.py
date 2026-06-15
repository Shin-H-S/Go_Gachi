"""drop generation logo columns

Revision ID: f9a8b7c6d5e4
Revises: 4789769ea16e
Create Date: 2026-06-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f9a8b7c6d5e4"
down_revision: str | Sequence[str] | None = "4789769ea16e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """로고 합성 기능 제거에 맞춰 더 이상 쓰지 않는 로고 메타데이터 컬럼을 삭제한다."""
    op.drop_column("generations", "logo_storage_key")
    op.drop_column("generations", "logo_image_hash")
    op.drop_column("generations", "logo_position")
    op.drop_column("generations", "has_logo")


def downgrade() -> None:
    """이전 버전으로 되돌릴 때 로고 메타데이터 컬럼을 복구한다."""
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
