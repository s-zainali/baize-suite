"""game tracking (game_type) + per-game rate options

Adds the current game being played to sessions (source of truth for the
frontend game tracking), a snapshot on the settled log, a per-game counter,
and per-game rate columns + a billing mode on the rate table.

Revision ID: b2e4c1a7d9f0
Revises: f7a1c0de9a01
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2e4c1a7d9f0'
down_revision = 'f7a1c0de9a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('play_session') as batch:
        batch.add_column(sa.Column('game_type', sa.String(length=30), nullable=True))
        batch.add_column(sa.Column('games_played', sa.Integer(), nullable=True, server_default='0'))

    with op.batch_alter_table('activity_log') as batch:
        batch.add_column(sa.Column('game_type', sa.String(length=30), nullable=True))

    with op.batch_alter_table('global_rate') as batch:
        batch.add_column(sa.Column('billing_mode', sa.String(length=12),
                                   nullable=False, server_default='per_minute'))
        batch.add_column(sa.Column('weekday_game_rate', sa.Integer(),
                                   nullable=False, server_default='0'))
        batch.add_column(sa.Column('weekend_game_rate', sa.Integer(),
                                   nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('global_rate') as batch:
        batch.drop_column('weekend_game_rate')
        batch.drop_column('weekday_game_rate')
        batch.drop_column('billing_mode')

    with op.batch_alter_table('activity_log') as batch:
        batch.drop_column('game_type')

    with op.batch_alter_table('play_session') as batch:
        batch.drop_column('games_played')
        batch.drop_column('game_type')