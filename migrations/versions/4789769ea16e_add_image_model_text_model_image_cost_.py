"""align api_usage model and cost columns

Revision ID: 4789769ea16e
Revises: c2f4a8b1d9e3
Create Date: 2026-06-11 18:34:02.658317

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4789769ea16e"
down_revision: str | Sequence[str] | None = "c2f4a8b1d9e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Bring already-migrated DBs in line with the current api_usage model."""
    op.execute("ALTER TABLE api_usage ADD COLUMN IF NOT EXISTS image_model VARCHAR(120)")
    op.execute("ALTER TABLE api_usage ADD COLUMN IF NOT EXISTS text_model VARCHAR(120)")
    op.execute(
        "ALTER TABLE api_usage "
        "ADD COLUMN IF NOT EXISTS image_cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0"
    )
    op.execute(
        "ALTER TABLE api_usage "
        "ADD COLUMN IF NOT EXISTS text_cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0"
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'api_usage'
                  AND column_name = 'model'
            ) THEN
                EXECUTE 'UPDATE api_usage SET image_model = COALESCE(image_model, model)';
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        UPDATE api_usage
        SET image_cost_usd = cost_usd
        WHERE image_cost_usd = 0
          AND cost_usd IS NOT NULL
        """
    )
    op.execute("UPDATE api_usage SET image_cost_usd = 0 WHERE image_cost_usd IS NULL")
    op.execute("UPDATE api_usage SET text_cost_usd = 0 WHERE text_cost_usd IS NULL")
    op.execute("ALTER TABLE api_usage ALTER COLUMN image_cost_usd SET DEFAULT 0")
    op.execute("ALTER TABLE api_usage ALTER COLUMN text_cost_usd SET DEFAULT 0")
    op.execute("ALTER TABLE api_usage ALTER COLUMN image_cost_usd SET NOT NULL")
    op.execute("ALTER TABLE api_usage ALTER COLUMN text_cost_usd SET NOT NULL")

    op.execute("DROP INDEX IF EXISTS ix_api_usage_model")
    op.execute("CREATE INDEX IF NOT EXISTS ix_api_usage_image_model ON api_usage (image_model)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_api_usage_text_model ON api_usage (text_model)")
    op.execute("ALTER TABLE api_usage DROP COLUMN IF EXISTS operation")
    op.execute("ALTER TABLE api_usage DROP COLUMN IF EXISTS model")


def downgrade() -> None:
    """Restore the previous api_usage column shape."""
    op.execute("ALTER TABLE api_usage ADD COLUMN IF NOT EXISTS model VARCHAR(120)")
    op.execute(
        "ALTER TABLE api_usage "
        "ADD COLUMN IF NOT EXISTS operation VARCHAR(80) NOT NULL DEFAULT 'image_edit'"
    )
    op.execute(
        """
        UPDATE api_usage
        SET model = COALESCE(model, image_model, text_model, 'unknown')
        """
    )
    op.execute("ALTER TABLE api_usage ALTER COLUMN model SET NOT NULL")
    op.execute("DROP INDEX IF EXISTS ix_api_usage_text_model")
    op.execute("DROP INDEX IF EXISTS ix_api_usage_image_model")
    op.execute("CREATE INDEX IF NOT EXISTS ix_api_usage_model ON api_usage (model)")
    op.execute("ALTER TABLE api_usage DROP COLUMN IF EXISTS text_cost_usd")
    op.execute("ALTER TABLE api_usage DROP COLUMN IF EXISTS image_cost_usd")
    op.execute("ALTER TABLE api_usage DROP COLUMN IF EXISTS text_model")
    op.execute("ALTER TABLE api_usage DROP COLUMN IF EXISTS image_model")
