"""sync Phase 2: sync_id + updated_at + deleted_at on syncable entities, + sync_cursor

Revision ID: e2c9f1a0dd45
Revises: d1a5e7c0ab34

Additive + idempotent. Adds the cross-boundary sync identity (sync_id), the
change watermark (updated_at), and soft-delete (deleted_at) where missing, then
backfills existing rows. Creates the local sync_cursor table.
"""
from alembic import op
import sqlalchemy as sa

revision = 'e2c9f1a0dd45'
down_revision = 'd1a5e7c0ab34'
branch_labels = None
depends_on = None

# every syncable table
SYNC_TABLES = [
    'pool_table', 'lounge', 'queue', 'play_session', 'session_player',
    'session_segment', 'booking', 'activity_log', 'canteen_product',
    'canteen_order', 'canteen_order_item', 'global_rate', 'customer',
]
# tables that don't yet have deleted_at
NEEDS_DELETED_AT = [
    'play_session', 'session_player', 'session_segment', 'activity_log',
    'canteen_order', 'canteen_order_item', 'global_rate', 'customer',
]


def _cols(insp, t):
    try:
        return {c['name'] for c in insp.get_columns(t)}
    except Exception:
        return None   # table missing


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    is_pg = bind.dialect.name == 'postgresql'
    new_uuid = "gen_random_uuid()::text" if is_pg else "lower(hex(randomblob(16)))"
    now_fn = "now()" if is_pg else "CURRENT_TIMESTAMP"

    for t in SYNC_TABLES:
        cols = _cols(insp, t)
        if cols is None:
            continue
        if 'sync_id' not in cols:
            op.add_column(t, sa.Column('sync_id', sa.String(length=36), nullable=True))
            op.create_index(f'ix_{t}_sync_id', t, ['sync_id'])
            op.execute(f"UPDATE {t} SET sync_id = {new_uuid} WHERE sync_id IS NULL")
        if 'updated_at' not in cols:
            op.add_column(t, sa.Column('updated_at', sa.DateTime(), nullable=True))
            # seed the watermark from created_at when present, else now
            src = 'created_at' if 'created_at' in cols else None
            op.execute(f"UPDATE {t} SET updated_at = COALESCE({src + ', ' if src else ''}{now_fn})")
        if t in NEEDS_DELETED_AT and 'deleted_at' not in cols:
            op.add_column(t, sa.Column('deleted_at', sa.DateTime(), nullable=True))

    if not insp.has_table('sync_cursor'):
        op.create_table(
            'sync_cursor',
            sa.Column('entity', sa.String(length=40), primary_key=True),
            sa.Column('last_pushed_at', sa.DateTime(), nullable=True),
            sa.Column('last_pulled_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if insp.has_table('sync_cursor'):
        op.drop_table('sync_cursor')
    for t in SYNC_TABLES:
        cols = _cols(insp, t)
        if cols is None:
            continue
        for col in ('sync_id', 'updated_at') + (('deleted_at',) if t in NEEDS_DELETED_AT else ()):
            if col in cols:
                if col == 'sync_id':
                    try: op.drop_index(f'ix_{t}_sync_id', table_name=t)
                    except Exception: pass
                op.drop_column(t, col)