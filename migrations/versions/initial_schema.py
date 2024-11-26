"""Initial schema

Revision ID: initial_schema
Revises: 
Create Date: 2024-11-26

"""
from alembic import op
import sqlalchemy as sa

revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # evaluation_metricsテーブルの変更
    op.execute("""
        ALTER TABLE evaluation_metrics
        ALTER COLUMN weight SET DEFAULT 1.0,
        ALTER COLUMN weight SET NOT NULL,
        ADD CONSTRAINT weight_range CHECK (weight >= 0.1 AND weight <= 2.0),
        ADD CONSTRAINT name_length CHECK (char_length(name) <= 100),
        ADD CONSTRAINT description_not_empty CHECK (description != ''),
        ADD CONSTRAINT category_valid CHECK (category IN ('core', 'custom'));
    """)

def downgrade() -> None:
    # 制約の削除
    op.execute("""
        ALTER TABLE evaluation_metrics
        DROP CONSTRAINT IF EXISTS weight_range,
        DROP CONSTRAINT IF EXISTS name_length,
        DROP CONSTRAINT IF EXISTS description_not_empty,
        DROP CONSTRAINT IF EXISTS category_valid,
        ALTER COLUMN weight DROP NOT NULL,
        ALTER COLUMN weight DROP DEFAULT;
    """)
