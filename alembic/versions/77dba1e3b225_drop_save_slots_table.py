"""drop_save_slots_table

Revision ID: 77dba1e3b225
Revises: 8fb692d90724
Create Date: 2026-03-02 19:01:32.937240

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77dba1e3b225'
down_revision: Union[str, Sequence[str], None] = '8fb692d90724'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """save_slots 테이블 삭제."""
    op.drop_table('save_slots')


def downgrade() -> None:
    """save_slots 테이블 복구."""
    op.create_table(
        'save_slots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_uid', sa.String(length=128), nullable=False, comment='소유 유저 UID'),
        sa.Column('slot_number', sa.Integer(), nullable=False, comment='슬롯 번호 (1~3)'),
        sa.Column('game_state', sa.JSON(), nullable=False, comment='LogicManager의 전체 state JSON'),
        sa.Column('play_day', sa.Integer(), nullable=False, comment='진행 일차 (목록 표시용)'),
        sa.Column('dungeon_level', sa.Integer(), nullable=False, comment='던전 레벨 (목록 표시용)'),
        sa.Column('monster_count', sa.Integer(), nullable=False, comment='생존 몬스터 수 (목록 표시용)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='최초 저장일'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='마지막 저장일'),
        sa.ForeignKeyConstraint(['user_uid'], ['users.uid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_uid', 'slot_number', name='uq_user_slot'),
    )
    op.create_index('ix_save_slots_user_uid', 'save_slots', ['user_uid'], unique=False)
