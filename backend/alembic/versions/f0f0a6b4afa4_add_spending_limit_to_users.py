"""add spending limit to users

Revision ID: f0f0a6b4afa4
Revises: ff7878a8f573
Create Date: 2025-10-17 17:09:26.508892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0f0a6b4afa4'
down_revision: Union[str, None] = 'ff7878a8f573'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add spending_limit_usd column (nullable, default None = unlimited)
    op.add_column('users', sa.Column('spending_limit_usd', sa.Float(), nullable=True))
    
    # Add total_spent_usd column to track current spending
    op.add_column('users', sa.Column('total_spent_usd', sa.Float(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'total_spent_usd')
    op.drop_column('users', 'spending_limit_usd')