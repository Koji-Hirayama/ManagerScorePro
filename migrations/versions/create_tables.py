"""Create initial tables

Revision ID: create_tables
Revises: initial_schema
Create Date: 2024-11-26

"""
from alembic import op
import sqlalchemy as sa

revision = 'create_tables'
down_revision = 'initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # managers テーブルの作成
    op.execute("""
    CREATE TABLE IF NOT EXISTS managers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        department VARCHAR(50) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # evaluations テーブルの作成
    op.execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
        id SERIAL PRIMARY KEY,
        manager_id INTEGER REFERENCES managers(id),
        evaluation_date DATE NOT NULL,
        communication_score NUMERIC(3,1) CHECK (communication_score BETWEEN 1 AND 5),
        support_score NUMERIC(3,1) CHECK (support_score BETWEEN 1 AND 5),
        goal_management_score NUMERIC(3,1) CHECK (goal_management_score BETWEEN 1 AND 5),
        leadership_score NUMERIC(3,1) CHECK (leadership_score BETWEEN 1 AND 5),
        problem_solving_score NUMERIC(3,1) CHECK (problem_solving_score BETWEEN 1 AND 5),
        strategy_score NUMERIC(3,1) CHECK (strategy_score BETWEEN 1 AND 5),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # evaluation_metrics テーブルの作成
    op.execute("""
    CREATE TABLE IF NOT EXISTS evaluation_metrics (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        category VARCHAR(20) NOT NULL,
        weight NUMERIC(3,1) DEFAULT 1.0,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS evaluations;")
    op.execute("DROP TABLE IF EXISTS managers;")
    op.execute("DROP TABLE IF EXISTS evaluation_metrics;")
