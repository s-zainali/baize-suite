"""per-game-type rates (game_rates JSON on global_rate)

Separate from b2e4c1a7d9f0 because that revision was already applied; this adds
the per-game-type rate map ({game_type: {weekday, weekend}}) on its own.

Revision ID: c7f3a9d1e05b
Revises: b2e4c1a7d9f0
"""
from alembic import op
import sqlalchemy as sa

revision = 'c7f3a9d1e05b'
down_revision = 'b2e4c1a7d9f0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('global_rate') as batch:
        batch.add_column(sa.Column('game_rates', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('global_rate') as batch:
        batch.drop_column('game_rates')