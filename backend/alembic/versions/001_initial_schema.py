"""initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('clerk_id', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('pan_number', sa.String(10), nullable=True),
        sa.Column('financial_year', sa.String(7), nullable=False, server_default='2024-25'),
        sa.Column('preferred_regime', sa.String(10), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        sa.UniqueConstraint('clerk_id', name='uq_users_clerk_id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_clerk_id', 'users', ['clerk_id'])
    op.create_index('ix_users_email_active', 'users', ['email', 'is_active'])

    op.create_table('user_preferences',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('theme', sa.String(10), nullable=False, server_default='dark'),
        sa.Column('language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_reports', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('ai_suggestions', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('dashboard_widgets', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_user_preferences_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_user_preferences'),
        sa.UniqueConstraint('user_id', name='uq_user_preferences_user_id'),
    )

    op.create_table('chat_sessions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False, server_default='New Chat'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('session_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_chat_sessions_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_chat_sessions'),
    )
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('ix_chat_sessions_user_updated', 'chat_sessions', ['user_id', 'updated_at'])

    op.create_table('chat_messages',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('rag_context_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('function_calls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('message_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], name='fk_chat_messages_session_id_chat_sessions', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_chat_messages'),
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_messages_session_created', 'chat_messages', ['session_id', 'created_at'])

    op.create_table('uploaded_documents',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('document_type', sa.String(30), nullable=False, server_default='other'),
        sa.Column('status', sa.String(20), nullable=False, server_default='uploaded'),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('chroma_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('financial_year', sa.String(7), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_uploaded_documents_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_uploaded_documents'),
    )
    op.create_index('ix_uploaded_documents_user_id', 'uploaded_documents', ['user_id'])

    op.create_table('saved_calculations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False, server_default='Tax Calculation'),
        sa.Column('financial_year', sa.String(7), nullable=False, server_default='2024-25'),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('old_regime_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_regime_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommended_regime', sa.String(10), nullable=True),
        sa.Column('tax_saved', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_saved_calculations_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_saved_calculations'),
    )
    op.create_index('ix_saved_calculations_user_id', 'saved_calculations', ['user_id'])

    op.create_table('tax_reports',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('financial_year', sa.String(7), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False, server_default='full_analysis'),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('report_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_ready', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_tax_reports_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_tax_reports'),
    )
    op.create_index('ix_tax_reports_user_id', 'tax_reports', ['user_id'])

    op.create_table('user_analytics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('session_id', sa.String(36), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_user_analytics_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_user_analytics'),
    )
    op.create_index('ix_user_analytics_user_id', 'user_analytics', ['user_id'])
    op.create_index('ix_user_analytics_event_type', 'user_analytics', ['event_type'])
    op.create_index('ix_user_analytics_created_at', 'user_analytics', ['created_at'])
    op.create_index('ix_analytics_user_type_date', 'user_analytics', ['user_id', 'event_type', 'created_at'])

    op.create_table('ai_sessions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('chat_session_id', sa.String(36), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('rag_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('function_calls_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_ai_sessions_user_id_users', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['chat_session_id'], ['chat_sessions.id'], name='fk_ai_sessions_chat_session_id_chat_sessions', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_ai_sessions'),
    )
    op.create_index('ix_ai_sessions_user_id', 'ai_sessions', ['user_id'])


def downgrade() -> None:
    op.drop_table('ai_sessions')
    op.drop_table('user_analytics')
    op.drop_table('tax_reports')
    op.drop_table('saved_calculations')
    op.drop_table('uploaded_documents')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('user_preferences')
    op.drop_table('users')
