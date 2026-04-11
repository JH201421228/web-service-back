"""rename_reaper_rooms_to_games

Revision ID: 67f165c8cb09
Revises: 20260412_0002
Create Date: 2026-04-12 03:16:59.255022

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67f165c8cb09'
down_revision: Union[str, Sequence[str], None] = '20260412_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename table reaper_rooms to reaper_games
    op.rename_table('reaper_rooms', 'reaper_games')
    
    # 2. Rename columns in reaper_games
    op.alter_column('reaper_games', 'name', new_column_name='title', existing_type=sa.String(100))
    op.alter_column('reaper_games', 'host_uid', new_column_name='creator_uid', existing_type=sa.String(128))
    op.alter_column('reaper_games', 'max_players', new_column_name='player_capacity', existing_type=sa.Integer())
    op.alter_column('reaper_games', 'bot_count', new_column_name='bot_total', existing_type=sa.Integer())

    # 3. Rename room_id to game_id in reaper_players
    # Note: MySQL/MariaDB handles the FK rename if we just rename the column, 
    # but we might need to drop and recreate the FK if it causes issues.
    # Usually, op.alter_column works fine for column renaming in modern Alembic/SQLAlchemy.
    op.alter_column('reaper_players', 'room_id', new_column_name='game_id', 
                    existing_type=sa.String(36), existing_nullable=False)


def downgrade() -> None:
    # Reverse operations
    op.alter_column('reaper_players', 'game_id', new_column_name='room_id', 
                    existing_type=sa.String(36), existing_nullable=False)
    
    op.alter_column('reaper_games', 'bot_total', new_column_name='bot_count', existing_type=sa.Integer())
    op.alter_column('reaper_games', 'player_capacity', new_column_name='max_players', existing_type=sa.Integer())
    op.alter_column('reaper_games', 'creator_uid', new_column_name='host_uid', existing_type=sa.String(128))
    op.alter_column('reaper_games', 'title', new_column_name='name', existing_type=sa.String(100))
    
    op.rename_table('reaper_games', 'reaper_rooms')
