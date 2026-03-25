"""add_news_comments_table

Revision ID: 5b72e3b9d2a1
Revises: e11dce88cd4f
Create Date: 2026-03-25 11:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b72e3b9d2a1'
down_revision: Union[str, Sequence[str], None] = 'e11dce88cd4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'news_comments',
        sa.Column('comment_id', sa.Integer(), nullable=False, comment='댓글 ID'),
        sa.Column('news_id', sa.Integer(), nullable=False, comment='뉴스 ID'),
        sa.Column('content', sa.String(length=500), nullable=False, comment='댓글 내용'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='작성일시'),
        sa.ForeignKeyConstraint(['news_id'], ['news.nid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('comment_id'),
    )
    op.create_index(op.f('ix_news_comments_news_id'), 'news_comments', ['news_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_news_comments_news_id'), table_name='news_comments')
    op.drop_table('news_comments')
