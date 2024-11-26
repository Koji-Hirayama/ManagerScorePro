"""Create evaluation metrics table

Revision ID: create_evaluation_metrics
Revises: initial_schema
Create Date: 2024-11-26

"""
from alembic import op
import sqlalchemy as sa

revision = 'create_evaluation_metrics'
down_revision = 'initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'evaluation_metrics',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('weight', sa.Float, nullable=False, server_default='1.0'),
        sa.CheckConstraint('weight >= 0.1 AND weight <= 2.0', name='weight_range'),
        sa.CheckConstraint('char_length(name) <= 100', name='name_length'),
        sa.CheckConstraint("description != ''", name='description_not_empty'),
        sa.CheckConstraint("category IN ('core', 'custom')", name='category_valid')
    )

    # デフォルトの評価指標を追加
    op.execute("""
        INSERT INTO evaluation_metrics (name, description, category, weight) VALUES
        ('コミュニケーション', 'チームメンバーとの効果的なコミュニケーション能力と、適切なフィードバックの提供', 'core', 1.0),
        ('リーダーシップ', 'チームを導き、メンバーの成長を支援する能力', 'core', 1.0),
        ('問題解決力', '課題の特定と効果的な解決策の実施能力', 'core', 1.0);
    """)

def downgrade() -> None:
    op.drop_table('evaluation_metrics')
