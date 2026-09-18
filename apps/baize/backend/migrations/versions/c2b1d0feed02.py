"""per-branch license storage (multi-branch Phase B)

Revision ID: c2b1d0feed02
Revises: b1a0c0ffee01
"""
from alembic import op
import sqlalchemy as sa

revision = 'c2b1d0feed02'
down_revision = 'b1a0c0ffee01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'branch_license',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('branch_uid', sa.String(length=50), nullable=False),
        sa.Column('club_uid', sa.String(length=80), nullable=False),
        sa.Column('name', sa.String(length=100), server_default='Branch'),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('entitlements', sa.Text(), server_default='[]'),
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('system_identifier', sa.Text(), nullable=True),
        sa.Column('server_status', sa.String(length=20), server_default='unknown'),
        sa.Column('server_checked_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('branch_uid', name='uq_branch_license_uid'),
    )
    op.create_index('ix_branch_license_branch_uid', 'branch_license', ['branch_uid'])
    op.create_index('ix_branch_license_club_uid', 'branch_license', ['club_uid'])


def downgrade():
    op.drop_index('ix_branch_license_club_uid', table_name='branch_license')
    op.drop_index('ix_branch_license_branch_uid', table_name='branch_license')
    op.drop_table('branch_license')