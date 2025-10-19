"""add comparisons table

Revision ID: 9690abbd48dd
Revises: f0f0a6b4afa4
Create Date: 2025-10-18 16:12:31.158967

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9690abbd48dd'
down_revision = 'f0f0a6b4afa4'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create comparisons table
    op.create_table(
        'comparisons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('prompt_text', sa.Text, nullable=False),
        sa.Column('models_used', sa.JSON, nullable=False),  # List of model IDs
        sa.Column('total_cost_usd', sa.Float, nullable=False, default=0.0),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Add comparison_id to requests table
    op.add_column('requests', sa.Column('comparison_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_requests_comparison_id', 'requests', 'comparisons', ['comparison_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_requests_comparison_id', 'requests', type_='foreignkey')
    op.drop_column('requests', 'comparison_id')
    op.drop_table('comparisons')
