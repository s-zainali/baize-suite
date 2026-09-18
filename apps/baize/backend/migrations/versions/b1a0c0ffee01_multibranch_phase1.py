"""multi-branch phase 1 — schema + default-branch backfill (no behaviour change)

Revision ID: b1a0c0ffee01
Revises: 1f6401e0c54b
"""
from alembic import op
import sqlalchemy as sa

revision = 'b1a0c0ffee01'
down_revision = '1f6401e0c54b'
branch_labels = None
depends_on = None

OPERATIONAL = ['queue', 'lounge', 'pool_table', 'play_session',
               'booking', 'activity_log', 'canteen_product', 'canteen_order']


def upgrade():
    # 1) branch + association tables
    op.create_table(
        'branch',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uid', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, server_default='Main Branch'),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(length=80), nullable=True),
        sa.UniqueConstraint('uid', name='uq_branch_uid'),
    )
    op.create_table(
        'user_branches',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], ['branch.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'branch_id'),
    )

    # 2) nullable branch_id on every operational table (+ index + FK)
    for t in OPERATIONAL:
        op.add_column(t, sa.Column('branch_id', sa.Integer(), nullable=True))
        op.create_index(f'ix_{t}_branch_id', t, ['branch_id'])
        op.create_foreign_key(f'fk_{t}_branch', t, 'branch', ['branch_id'], ['id'])

    # 3) user home branch
    op.add_column('user', sa.Column('primary_branch_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_user_primary_branch', 'user', 'branch', ['primary_branch_id'], ['id'])

    # 4) backfill — one default branch, every existing row + user attached to it
    # op.execute(
    #     "INSERT INTO branch (uid, name, is_default, status, sort_order, created_at) "
    #     "VALUES ('main', 'Main Branch', true, 'active', 0, now())"
    # )
    for t in OPERATIONAL:
        op.execute(
            f"UPDATE {t} SET branch_id = (SELECT id FROM branch WHERE is_default LIMIT 1) "
            f"WHERE branch_id IS NULL"
        )
    op.execute(
        'UPDATE "user" SET primary_branch_id = (SELECT id FROM branch WHERE is_default LIMIT 1) '
        'WHERE primary_branch_id IS NULL'
    )
    op.execute(
        'INSERT INTO user_branches (user_id, branch_id) '
        'SELECT u.id, (SELECT id FROM branch WHERE is_default LIMIT 1) FROM "user" u '
        'WHERE NOT EXISTS (SELECT 1 FROM user_branches ub WHERE ub.user_id = u.id)'
    )
    # branch_id stays NULLABLE in Phase 1 — a later migration tightens it to
    # NOT NULL once the app writes branch_id on every insert (Phase 2).


def downgrade():
    op.drop_constraint('fk_user_primary_branch', 'user', type_='foreignkey')
    op.drop_column('user', 'primary_branch_id')
    for t in OPERATIONAL:
        op.drop_constraint(f'fk_{t}_branch', t, type_='foreignkey')
        op.drop_index(f'ix_{t}_branch_id', table_name=t)
        op.drop_column(t, 'branch_id')
    op.drop_table('user_branches')
    op.drop_table('branch')