"""empty message

Revision ID: cd2cb531dc03
Revises: e8c0b64339ad
Create Date: 2026-09-06 21:45:29.340114

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'cd2cb531dc03'
down_revision = 'e8c0b64339ad'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Helper to check if column exists on a table
    def column_exists(table_name, column_name):
        return any(col['name'] == column_name for col in inspector.get_columns(table_name))

    # Helper to check if unique constraint/index exists
    def constraint_exists(table_name, constraint_name):
        for const in inspector.get_unique_constraints(table_name):
            if const['name'] == constraint_name:
                return True
        for idx in inspector.get_indexes(table_name):
            if idx['name'] == constraint_name:
                return True
        return False

    # 1. booking
    with op.batch_alter_table('booking', schema=None) as batch_op:
        if not column_exists('booking', 'deleted_at'):
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        if not column_exists('booking', 'deleted_by'):
            batch_op.add_column(sa.Column('deleted_by', sa.String(length=80), nullable=True))

    # 2. canteen_product
    with op.batch_alter_table('canteen_product', schema=None) as batch_op:
        if not column_exists('canteen_product', 'deleted_at'):
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        if not column_exists('canteen_product', 'deleted_by'):
            batch_op.add_column(sa.Column('deleted_by', sa.String(length=80), nullable=True))

    # 3. lounge
    with op.batch_alter_table('lounge', schema=None) as batch_op:
        if not column_exists('lounge', 'deleted_at'):
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        if not column_exists('lounge', 'deleted_by'):
            batch_op.add_column(sa.Column('deleted_by', sa.String(length=80), nullable=True))
        
        if not column_exists('lounge', 'uid'):
            batch_op.add_column(sa.Column('uid', sa.String(length=50), server_default="lounge-0000000000000", nullable=False))
        
        if not column_exists('lounge', 'status'):
            batch_op.add_column(sa.Column('status', sa.String(length=20), server_default="active", nullable=False))
            
        if not column_exists('lounge', 'sort_order'):
            batch_op.add_column(sa.Column('sort_order', sa.Integer(), nullable=True))
            
    # Handle random UID backfill for any existing rows where uid starts with default or is null/empty
    conn.execute(sa.text("""
        UPDATE lounge 
        SET uid = 'lounge-' || floor(random() * 9000000000000 + 1000000000000)::text 
        WHERE uid IS NULL OR uid = '' OR uid LIKE 'lounge-0000%'
    """))

    with op.batch_alter_table('lounge', schema=None) as batch_op:
        if not constraint_exists('lounge', 'uq_lounge_uid'):
            # Name the unique constraint explicitly so it's safely checkable
            batch_op.create_unique_constraint('uq_lounge_uid', ['uid'])

    # 4. pool_table
    with op.batch_alter_table('pool_table', schema=None) as batch_op:
        if not column_exists('pool_table', 'deleted_at'):
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        if not column_exists('pool_table', 'deleted_by'):
            batch_op.add_column(sa.Column('deleted_by', sa.String(length=80), nullable=True))
        if not column_exists('pool_table', 'lounge_uid'):
            batch_op.add_column(sa.Column('lounge_uid', sa.String(), nullable=True))
            
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(),
               nullable=False)
               
        # Safely drop foreign key if it exists
        fkeys = [fk['name'] for fk in inspector.get_foreign_keys('pool_table')]
        if 'pool_table_lounge_id_fkey' in fkeys:
            batch_op.drop_constraint('pool_table_lounge_id_fkey', type_='foreignkey')
            
        # Create new FK if not already pointing to lounge(uid)
        has_uid_fk = any(fk.get('referred_columns') == ['uid'] for fk in inspector.get_foreign_keys('pool_table'))
        if not has_uid_fk:
            batch_op.create_foreign_key('fk_pool_table_lounge_uid', 'lounge', ['lounge_uid'], ['uid'])
            
        if column_exists('pool_table', 'lounge_id'):
            batch_op.drop_column('lounge_id')

    # 5. queue
    with op.batch_alter_table('queue', schema=None) as batch_op:
        if not column_exists('queue', 'deleted_at'):
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        if not column_exists('queue', 'deleted_by'):
            batch_op.add_column(sa.Column('deleted_by', sa.String(length=80), nullable=True))

    # 6. user
    with op.batch_alter_table('user', schema=None) as batch_op:
        if not column_exists('user', 'deleted_at'):
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        if not column_exists('user', 'deleted_by'):
            batch_op.add_column(sa.Column('deleted_by', sa.String(length=80), nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('deleted_by')
        batch_op.drop_column('deleted_at')

    with op.batch_alter_table('queue', schema=None) as batch_op:
        batch_op.drop_column('deleted_by')
        batch_op.drop_column('deleted_at')

    with op.batch_alter_table('pool_table', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lounge_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.drop_constraint('fk_pool_table_lounge_uid', type_='foreignkey')
        batch_op.create_foreign_key('pool_table_lounge_id_fkey', 'lounge', ['lounge_id'], ['id'])
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(),
               nullable=True)
        batch_op.drop_column('lounge_uid')
        batch_op.drop_column('deleted_by')
        batch_op.drop_column('deleted_at')

    with op.batch_alter_table('lounge', schema=None) as batch_op:
        batch_op.drop_constraint('uq_lounge_uid', type_='unique')
        batch_op.drop_column('sort_order')
        batch_op.drop_column('status')
        batch_op.drop_column('uid')
        batch_op.drop_column('deleted_by')
        batch_op.drop_column('deleted_at')

    with op.batch_alter_table('canteen_product', schema=None) as batch_op:
        batch_op.drop_column('deleted_by')
        batch_op.drop_column('deleted_at')

    with op.batch_alter_table('booking', schema=None) as batch_op:
        batch_op.drop_column('deleted_by')
        batch_op.drop_column('deleted_at')