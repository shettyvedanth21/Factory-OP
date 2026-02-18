"""Initial schema - create all tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # factories table
    op.create_table(
        'factories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False, unique=True),
        sa.Column('timezone', sa.String(length=100), default='UTC'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('factory_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('whatsapp_number', sa.String(length=50)),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('super_admin', 'admin', name='userrole'), nullable=False),
        sa.Column('permissions', sa.JSON()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('invite_token', sa.String(length=255)),
        sa.Column('invited_at', sa.DateTime()),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('factory_id', 'email', name='uq_factory_email')
    )
    op.create_index('ix_users_factory_id', 'users', ['factory_id'])

    # devices table
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('factory_id', sa.Integer(), nullable=False),
        sa.Column('device_key', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255)),
        sa.Column('manufacturer', sa.String(length=255)),
        sa.Column('model', sa.String(length=255)),
        sa.Column('region', sa.String(length=255)),
        sa.Column('api_key', sa.String(length=255)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_seen', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('factory_id', 'device_key', name='uq_factory_device')
    )
    op.create_index('ix_devices_factory_id', 'devices', ['factory_id'])

    # device_parameters table
    op.create_table(
        'device_parameters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('factory_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('parameter_key', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255)),
        sa.Column('unit', sa.String(length=50)),
        sa.Column('data_type', sa.Enum('float', 'int', 'string', name='datatype'), default='float'),
        sa.Column('is_kpi_selected', sa.Boolean(), default=True),
        sa.Column('discovered_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id']),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id', 'parameter_key', name='uq_device_param')
    )
    op.create_index('ix_device_parameters_factory_id', 'device_parameters', ['factory_id', 'device_id'])
    op.create_index('ix_device_parameters_device_param', 'device_parameters', ['device_id', 'parameter_key'])

    # rules table
    op.create_table(
        'rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('factory_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('scope', sa.Enum('device', 'global', name='rulescope'), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=False),
        sa.Column('cooldown_minutes', sa.Integer(), default=15),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('schedule_type', sa.Enum('always', 'time_window', 'date_range', name='scheduletype'), default='always'),
        sa.Column('schedule_config', sa.JSON()),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='severity'), default='medium'),
        sa.Column('notification_channels', sa.JSON()),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rules_factory_active', 'rules', ['factory_id', 'is_active'])

    # rule_devices association table
    op.create_table(
        'rule_devices',
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['rules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('rule_id', 'device_id')
    )

    # alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('factory_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('message', sa.Text()),
        sa.Column('telemetry_snapshot', sa.JSON()),
        sa.Column('notification_sent', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id']),
        sa.ForeignKeyConstraint(['rule_id'], ['rules.id']),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alerts_factory_device_time', 'alerts', ['factory_id', 'device_id', 'triggered_at'])
    op.create_index('ix_alerts_factory_time', 'alerts', ['factory_id', 'triggered_at'])

    # rule_cooldowns table
    op.create_table(
        'rule_cooldowns',
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('last_triggered', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['rules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('rule_id', 'device_id')
    )

    # analytics_jobs table
    op.create_table(
        'analytics_jobs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('factory_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('mode', sa.String(20), default='standard'),
        sa.Column('device_ids', sa.JSON(), nullable=False),
        sa.Column('date_range_start', sa.DateTime(), nullable=False),
        sa.Column('date_range_end', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('result_url', sa.String(500)),
        sa.Column('error_message', sa.Text()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analytics_jobs_factory_status', 'analytics_jobs', ['factory_id', 'status'])

    # reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('factory_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255)),
        sa.Column('device_ids', sa.JSON(), nullable=False),
        sa.Column('date_range_start', sa.DateTime(), nullable=False),
        sa.Column('date_range_end', sa.DateTime(), nullable=False),
        sa.Column('format', sa.String(20), nullable=False),
        sa.Column('include_analytics', sa.Boolean(), default=False),
        sa.Column('analytics_job_id', sa.String(36)),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('file_url', sa.String(500)),
        sa.Column('file_size_bytes', sa.BigInteger()),
        sa.Column('error_message', sa.Text()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('reports')
    op.drop_table('analytics_jobs')
    op.drop_table('rule_cooldowns')
    op.drop_table('alerts')
    op.drop_table('rule_devices')
    op.drop_table('rules')
    op.drop_table('device_parameters')
    op.drop_table('devices')
    op.drop_table('users')
    op.drop_table('factories')
