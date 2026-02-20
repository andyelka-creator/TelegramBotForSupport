"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-02-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role_enum = sa.Enum('ADMIN', 'SYSADMIN', name='role_enum', create_type=False)
    task_type_enum = sa.Enum('ISSUE_NEW', 'REPLACE_DAMAGED', 'TOPUP', name='task_type_enum', create_type=False)
    task_status_enum = sa.Enum(
        'CREATED',
        'DATA_COLLECTED',
        'IN_PROGRESS',
        'DONE_BY_SYSADMIN',
        'CONFIRMED',
        'CLOSED',
        'CANCELLED',
        name='task_status_enum',
        create_type=False,
    )
    execution_mode_enum = sa.Enum('ASSISTED', name='execution_mode_enum', create_type=False)

    bind = op.get_bind()
    role_enum.create(bind, checkfirst=True)
    task_type_enum.create(bind, checkfirst=True)
    task_status_enum.create(bind, checkfirst=True)
    execution_mode_enum.create(bind, checkfirst=True)

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('role', role_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

    op.create_table(
        'tasks',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('type', task_type_enum, nullable=False),
        sa.Column('status', task_status_enum, nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('assigned_to', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('execution_mode', execution_mode_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'task_data',
        sa.Column('task_id', sa.Uuid(), sa.ForeignKey('tasks.id'), primary_key=True),
        sa.Column('json_data', sa.JSON(), nullable=False),
    )

    op.create_table(
        'invite_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.Uuid(), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('token', sa.Uuid(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_invite_tokens_task_id', 'invite_tokens', ['task_id'])
    op.create_index('ix_invite_tokens_token', 'invite_tokens', ['token'], unique=True)

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.Uuid(), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
    )
    op.create_index('ix_audit_log_task_id', 'audit_log', ['task_id'])


def downgrade() -> None:
    op.drop_index('ix_audit_log_task_id', table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_index('ix_invite_tokens_token', table_name='invite_tokens')
    op.drop_index('ix_invite_tokens_task_id', table_name='invite_tokens')
    op.drop_table('invite_tokens')
    op.drop_table('task_data')
    op.drop_table('tasks')
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_table('users')

    bind = op.get_bind()
    sa.Enum(name='execution_mode_enum').drop(bind, checkfirst=True)
    sa.Enum(name='task_status_enum').drop(bind, checkfirst=True)
    sa.Enum(name='task_type_enum').drop(bind, checkfirst=True)
    sa.Enum(name='role_enum').drop(bind, checkfirst=True)
