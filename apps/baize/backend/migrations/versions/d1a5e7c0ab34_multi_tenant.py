"""multi-tenant Phase 1: club_uid on every tenant table (RLS foundation)

Revision ID: d1a5e7c0ab34
Revises: c2b1d0feed02

On Postgres the column DEFAULTs to current_setting('app.club_uid', true) so the
DB stamps each insert with the request's pinned tenant (see tenancy.py). RLS
policies themselves are installed at cloud startup (enable_rls), not here, so a
local single-tenant install is completely unaffected by this migration.
"""
from alembic import op
import sqlalchemy as sa

revision = 'd1a5e7c0ab34'
down_revision = 'c2b1d0feed02'
branch_labels = None
depends_on = None

TENANT_TABLES = [
    'branch', 'queue', 'lounge', 'pool_table', 'play_session', 'session_player',
    'session_segment', 'customer', 'password_reset_code', 'global_rate', 'table_type',
    'booking', 'activity_log', 'canteen_product', 'canteen_order', 'settings',
    'canteen_order_item', 'payment_intent', 'license', 'branch_license', 'user',
]


def _has_table(insp, t):
    try:
        return insp.has_table(t)
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    is_pg = bind.dialect.name == 'postgresql'
    for t in TENANT_TABLES:
        if not _has_table(insp, t):
            continue
        cols = {c['name'] for c in insp.get_columns(t)}
        if 'club_uid' in cols:
            continue
        # Postgres: default the tenant from the pinned session var, so ORM inserts
        # (which don't know about club_uid) still get stamped. SQLite/others: a
        # plain nullable column (local dev — RLS/tenancy never runs there).
        server_default = sa.text("current_setting('app.club_uid', true)") if is_pg else None
        op.add_column(t, sa.Column('club_uid', sa.String(length=80),
                                   nullable=True, server_default=server_default))
        op.create_index(f'ix_{t}_club_uid', t, ['club_uid'])


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for t in TENANT_TABLES:
        if not _has_table(insp, t):
            continue
        cols = {c['name'] for c in insp.get_columns(t)}
        if 'club_uid' not in cols:
            continue
        try:
            op.drop_index(f'ix_{t}_club_uid', table_name=t)
        except Exception:
            pass
        op.drop_column(t, 'club_uid')