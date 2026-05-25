"""Initial migration with all tables and indexes

Revision ID: 000000000001
Revises: 
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000000000001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_users_username', 'users', ['username'])

    # documents
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('upload_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('uploaded_by', sa.String(100)),
    )

    # document_chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('embedding', sa.NullType()),  # vector(768) - handled via raw SQL below
        sa.Column('chunk_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
    )
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    # pgvector IVF index
    op.execute("CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops)")

    # chat_logs
    op.create_table(
        'chat_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('tg_user_id', sa.BigInteger(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text()),
        sa.Column('status', sa.String(20), nullable=False, server_default='ANSWERED'),
        sa.Column('similarity_score', sa.Float()),
        sa.Column('response_time_ms', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_chat_logs_created_at', 'chat_logs', ['created_at'])
    op.create_index('ix_chat_logs_status', 'chat_logs', ['status'])
    op.create_index('ix_chat_logs_tg_user_id', 'chat_logs', ['tg_user_id'])

    # fallback_queue
    op.create_table(
        'fallback_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('chat_log_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_logs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tg_user_id', sa.BigInteger(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('assigned_to', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('resolved_at', sa.DateTime()),
    )
    op.create_index('ix_fallback_queue_status', 'fallback_queue', ['status'])
    op.create_index('ix_fallback_queue_chat_log_id', 'fallback_queue', ['chat_log_id'])

    # audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(100)),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', sa.String(100)),
        sa.Column('details', postgresql.JSONB(), server_default='{}'),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('fallback_queue')
    op.drop_table('chat_logs')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('users')
