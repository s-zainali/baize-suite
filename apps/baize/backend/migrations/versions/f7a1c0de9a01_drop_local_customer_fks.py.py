"""Drop local customer_id FKs — customers live in the central app now.

PlaySession / SessionPlayer / Booking store the CENTRAL customer id, which has
no matching row in the local `customer` table, so the old FK constraints
rejected the write (a session started from a booking couldn't link its member,
and the game never logged). Dropping the constraints; the column stays a plain
indexed integer.
"""
from alembic import op

revision = 'f7a1c0de9a01'
down_revision = 'd1332c44f0db'
branch_labels = None
depends_on = None

_TABLES = ('play_session', 'session_player', 'booking')


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return  # SQLite doesn't enforce these FKs; nothing to drop
    for tbl in _TABLES:
        op.execute(f'ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {tbl}_customer_id_fkey')


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return
    for tbl in _TABLES:
        op.execute(
            f'ALTER TABLE {tbl} ADD CONSTRAINT {tbl}_customer_id_fkey '
            f'FOREIGN KEY (customer_id) REFERENCES customer (id)')