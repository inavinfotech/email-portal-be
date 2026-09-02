"""Add CC and BCC columns to email_logs table

Revision ID: 002_add_cc_bcc_to_email_logs
Revises: 001_initial_schema
Create Date: 2026-09-02 14:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_cc_bcc_to_email_logs'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('email_logs', sa.Column('cc', sa.Text(), nullable=True))
    op.add_column('email_logs', sa.Column('bcc', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('email_logs', 'bcc')
    op.drop_column('email_logs', 'cc')
