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
    # このマイグレーションは空にする（制約は create_evaluation_metrics.py で作成される）
    pass

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
