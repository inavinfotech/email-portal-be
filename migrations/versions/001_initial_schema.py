"""Initial database schema for portal-email

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-07-26 13:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. smtp_configs table
    op.create_table(
        'smtp_configs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('host', sa.String(), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False, server_default='587'),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('from_email', sa.String(), nullable=False),
        sa.Column('from_name', sa.String(), nullable=False, server_default='Email Portal'),
        sa.Column('use_tls', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('use_ssl', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('last_tested_at', sa.DateTime(), nullable=True),
        sa.Column('test_status', sa.String(), server_default='untested'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. applications table
    op.create_table(
        'applications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(), nullable=False),
        sa.Column('api_secret', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('allowed_domains', sa.Text(), server_default='["*"]'),
        sa.Column('rate_limit', sa.Integer(), server_default='50'),
        sa.Column('smtp_config_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['smtp_config_id'], ['smtp_configs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key')
    )

    # 3. email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('html_body', sa.Text(), nullable=False),
        sa.Column('text_body', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=False, server_default='transactional'),
        sa.Column('variables', sa.Text(), server_default='[]'),
        sa.Column('is_builtin', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('created_by', sa.String(), server_default='admin'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # 4. email_logs table
    op.create_table(
        'email_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('app_id', sa.String(), nullable=True),
        sa.Column('template_id', sa.String(), nullable=True),
        sa.Column('smtp_config_id', sa.String(), nullable=True),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('recipient_name', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), server_default='{}'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['app_id'], ['applications.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. otp_records table
    op.create_table(
        'otp_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('app_id', sa.String(), nullable=True),
        sa.Column('identifier', sa.String(), nullable=False),
        sa.Column('otp_code', sa.String(), nullable=False),
        sa.Column('purpose', sa.String(), nullable=False, server_default='login'),
        sa.Column('attempts', sa.Integer(), server_default='0'),
        sa.Column('max_attempts', sa.Integer(), server_default='3'),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['app_id'], ['applications.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('otp_records')
    op.drop_table('email_logs')
    op.drop_table('email_templates')
    op.drop_table('applications')
    op.drop_table('smtp_configs')
