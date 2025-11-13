"""replace_preference_with_global_and_route_preferences

Revision ID: 172fc263f6cb
Revises: ecd62863c9d0
Create Date: 2025-11-13 11:51:48.867956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '172fc263f6cb'
down_revision: Union[str, Sequence[str], None] = 'ecd62863c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old preference table
    op.drop_index(op.f('ix_preference_user_id'), table_name='preference')
    op.drop_index(op.f('ix_preference_id'), table_name='preference')
    op.drop_table('preference')
    
    # Create the new global_preferences table
    op.create_table('global_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('prompt', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_global_preferences_id'), 'global_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_global_preferences_user_id'), 'global_preferences', ['user_id'], unique=False)
    
    # Create the new route_preferences table
    op.create_table('route_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('prompt', sa.String(), nullable=False),
        sa.Column('from_latitude', sa.Float(), nullable=False),
        sa.Column('from_longitude', sa.Float(), nullable=False),
        sa.Column('to_latitude', sa.Float(), nullable=False),
        sa.Column('to_longitude', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_route_preferences_id'), 'route_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_route_preferences_user_id'), 'route_preferences', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the new tables
    op.drop_index(op.f('ix_route_preferences_user_id'), table_name='route_preferences')
    op.drop_index(op.f('ix_route_preferences_id'), table_name='route_preferences')
    op.drop_table('route_preferences')
    
    op.drop_index(op.f('ix_global_preferences_user_id'), table_name='global_preferences')
    op.drop_index(op.f('ix_global_preferences_id'), table_name='global_preferences')
    op.drop_table('global_preferences')
    
    # Recreate the old preference table
    op.create_table('preference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('prompt', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_preference_id'), 'preference', ['id'], unique=False)
    op.create_index(op.f('ix_preference_user_id'), 'preference', ['user_id'], unique=False)
