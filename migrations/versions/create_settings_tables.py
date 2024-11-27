"""Create settings tables

Revision ID: create_settings_tables
Revises: create_evaluation_metrics
Create Date: 2024-11-27

"""
from alembic import op
import sqlalchemy as sa

revision = 'create_settings_tables'
down_revision = 'create_evaluation_metrics'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ai_model_config テーブルの作成
    op.execute("""
    CREATE TABLE IF NOT EXISTS ai_model_config (
        id SERIAL PRIMARY KEY,
        model_name VARCHAR(50) NOT NULL DEFAULT 'gpt-4',
        temperature NUMERIC(3,2) NOT NULL DEFAULT 0.7 CHECK (temperature >= 0.0 AND temperature <= 2.0),
        max_tokens INTEGER NOT NULL DEFAULT 2000 CHECK (max_tokens >= 100 AND max_tokens <= 4000)
    );
    """)

    # cache_config テーブルの作成
    op.execute("""
    CREATE TABLE IF NOT EXISTS cache_config (
        id SERIAL PRIMARY KEY,
        enabled BOOLEAN NOT NULL DEFAULT true,
        ttl_minutes INTEGER NOT NULL DEFAULT 60 CHECK (ttl_minutes >= 1 AND ttl_minutes <= 1440),
        max_size_mb INTEGER NOT NULL DEFAULT 100 CHECK (max_size_mb >= 1 AND max_size_mb <= 1000)
    );
    """)

    # デフォルト設定の挿入
    op.execute("""
    INSERT INTO ai_model_config (model_name, temperature, max_tokens)
    VALUES ('gpt-4', 0.7, 2000)
    ON CONFLICT DO NOTHING;
    """)

    op.execute("""
    INSERT INTO cache_config (enabled, ttl_minutes, max_size_mb)
    VALUES (true, 60, 100)
    ON CONFLICT DO NOTHING;
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cache_config;")
    op.execute("DROP TABLE IF EXISTS ai_model_config;")
