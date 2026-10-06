"""Genesis schema baseline
Revision ID: g0001
Revises:
Create Date: 2026-10-06 21:23:55.177164
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('actual_observations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('business_id', sa.String(), nullable=False),
    sa.Column('key', sa.String(length=120), nullable=False),
    sa.Column('value', sa.String(length=120), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_actual_observations_business_id'), 'actual_observations', ['business_id'], unique=False)
    op.create_index(op.f('ix_actual_observations_key'), 'actual_observations', ['key'], unique=False)
    op.create_index(op.f('ix_actual_observations_tenant_id'), 'actual_observations', ['tenant_id'], unique=False)
    op.create_table('audit_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('actor_id', sa.String(), nullable=False),
    sa.Column('action', sa.String(length=120), nullable=False),
    sa.Column('resource_type', sa.String(length=80), nullable=False),
    sa.Column('resource_id', sa.String(length=80), nullable=False),
    sa.Column('details_json', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_events_actor_id'), 'audit_events', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_events_tenant_id'), 'audit_events', ['tenant_id'], unique=False)
    op.create_table('businesses',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('lifecycle_state', sa.String(length=40), nullable=False),
    sa.Column('twin_json', sa.Text(), nullable=False),
    sa.Column('twin_version', sa.Integer(), nullable=False),
    sa.Column('proof_state_json', sa.Text(), nullable=False),
    sa.Column('route_context_json', sa.Text(), nullable=False),
    sa.Column('next_turn_json', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_businesses_tenant_id'), 'businesses', ['tenant_id'], unique=False)
    op.create_table('community_blocks',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('blocker_user_id', sa.String(), nullable=False),
    sa.Column('blocked_user_id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('blocker_user_id', 'blocked_user_id')
    )
    op.create_index(op.f('ix_community_blocks_blocked_user_id'), 'community_blocks', ['blocked_user_id'], unique=False)
    op.create_index(op.f('ix_community_blocks_blocker_user_id'), 'community_blocks', ['blocker_user_id'], unique=False)
    op.create_table('community_posts',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('display_name', sa.String(), nullable=False),
    sa.Column('category', sa.String(), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('moderation_status', sa.String(length=24), nullable=False),
    sa.Column('deleted', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_community_posts_deleted'), 'community_posts', ['deleted'], unique=False)
    op.create_index(op.f('ix_community_posts_moderation_status'), 'community_posts', ['moderation_status'], unique=False)
    op.create_index(op.f('ix_community_posts_tenant_id'), 'community_posts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_community_posts_user_id'), 'community_posts', ['user_id'], unique=False)
    op.create_table('community_replies',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('post_id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('display_name', sa.String(), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('moderation_status', sa.String(length=24), nullable=False),
    sa.Column('deleted', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_community_replies_deleted'), 'community_replies', ['deleted'], unique=False)
    op.create_index(op.f('ix_community_replies_moderation_status'), 'community_replies', ['moderation_status'], unique=False)
    op.create_index(op.f('ix_community_replies_post_id'), 'community_replies', ['post_id'], unique=False)
    op.create_index(op.f('ix_community_replies_tenant_id'), 'community_replies', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_community_replies_user_id'), 'community_replies', ['user_id'], unique=False)
    op.create_table('community_reports',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('reporter_user_id', sa.String(), nullable=False),
    sa.Column('target_type', sa.String(length=20), nullable=False),
    sa.Column('target_id', sa.String(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_community_reports_reporter_user_id'), 'community_reports', ['reporter_user_id'], unique=False)
    op.create_index(op.f('ix_community_reports_status'), 'community_reports', ['status'], unique=False)
    op.create_index(op.f('ix_community_reports_target_id'), 'community_reports', ['target_id'], unique=False)
    op.create_table('decision_ledger',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('business_id', sa.String(), nullable=False),
    sa.Column('decision_id', sa.String(), nullable=False),
    sa.Column('payload_hash', sa.String(length=64), nullable=False),
    sa.Column('payload_json', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decision_ledger_business_id'), 'decision_ledger', ['business_id'], unique=False)
    op.create_index(op.f('ix_decision_ledger_decision_id'), 'decision_ledger', ['decision_id'], unique=False)
    op.create_index(op.f('ix_decision_ledger_tenant_id'), 'decision_ledger', ['tenant_id'], unique=False)
    op.create_table('decisions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('business_id', sa.String(), nullable=False),
    sa.Column('question', sa.Text(), nullable=False),
    sa.Column('risk_tier', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('recommendation_json', sa.Text(), nullable=False),
    sa.Column('approved_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decisions_business_id'), 'decisions', ['business_id'], unique=False)
    op.create_index(op.f('ix_decisions_tenant_id'), 'decisions', ['tenant_id'], unique=False)
    op.create_table('evidence',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('business_id', sa.String(), nullable=False),
    sa.Column('classification', sa.String(length=40), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('source_ref', sa.Text(), nullable=False),
    sa.Column('confidence', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_business_id'), 'evidence', ['business_id'], unique=False)
    op.create_index(op.f('ix_evidence_tenant_id'), 'evidence', ['tenant_id'], unique=False)
    op.create_table('execution_action_records',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('business_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('point_key', sa.String(length=80), nullable=False),
    sa.Column('mode', sa.String(length=16), nullable=False),
    sa.Column('risk_tier', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('payload_json', sa.Text(), nullable=False),
    sa.Column('result_json', sa.Text(), nullable=False),
    sa.Column('idempotency_key', sa.String(length=80), nullable=False),
    sa.Column('approved_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('dispatch_started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('provider_reference', sa.Text(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_execution_action_records_business_id'), 'execution_action_records', ['business_id'], unique=False)
    op.create_index(op.f('ix_execution_action_records_idempotency_key'), 'execution_action_records', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_execution_action_records_point_key'), 'execution_action_records', ['point_key'], unique=False)
    op.create_index(op.f('ix_execution_action_records_status'), 'execution_action_records', ['status'], unique=False)
    op.create_index(op.f('ix_execution_action_records_tenant_id'), 'execution_action_records', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_execution_action_records_user_id'), 'execution_action_records', ['user_id'], unique=False)
    op.create_table('execution_receipt_records',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('business_id', sa.String(), nullable=False),
    sa.Column('action_id', sa.String(), nullable=False),
    sa.Column('evidence_type', sa.String(length=80), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('external_reference', sa.Text(), nullable=True),
    sa.Column('metadata_json', sa.Text(), nullable=False),
    sa.Column('provenance', sa.String(length=24), nullable=False),
    sa.Column('trusted', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_execution_receipt_records_action_id'), 'execution_receipt_records', ['action_id'], unique=False)
    op.create_index(op.f('ix_execution_receipt_records_business_id'), 'execution_receipt_records', ['business_id'], unique=False)
    op.create_index(op.f('ix_execution_receipt_records_evidence_type'), 'execution_receipt_records', ['evidence_type'], unique=False)
    op.create_index(op.f('ix_execution_receipt_records_provenance'), 'execution_receipt_records', ['provenance'], unique=False)
    op.create_index(op.f('ix_execution_receipt_records_tenant_id'), 'execution_receipt_records', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_execution_receipt_records_trusted'), 'execution_receipt_records', ['trusted'], unique=False)
    op.create_table('execution_tasks',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('business_id', sa.String(), nullable=False),
    sa.Column('horizon', sa.String(length=32), nullable=False),
    sa.Column('task', sa.Text(), nullable=False),
    sa.Column('budget', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('kpi', sa.String(length=200), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_execution_tasks_business_id'), 'execution_tasks', ['business_id'], unique=False)
    op.create_index(op.f('ix_execution_tasks_tenant_id'), 'execution_tasks', ['tenant_id'], unique=False)
    op.create_table('founder_profiles',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('owner_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('objective', sa.Text(), nullable=True),
    sa.Column('constraints_json', sa.Text(), nullable=False),
    sa.Column('profile_json', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_founder_profiles_owner_id'), 'founder_profiles', ['owner_id'], unique=False)
    op.create_index(op.f('ix_founder_profiles_tenant_id'), 'founder_profiles', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_founder_profiles_user_id'), 'founder_profiles', ['user_id'], unique=False)
    op.create_table('provider_webhook_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=True),
    sa.Column('provider', sa.String(length=32), nullable=False),
    sa.Column('event_id', sa.String(length=160), nullable=False),
    sa.Column('event_type', sa.String(length=120), nullable=False),
    sa.Column('verified_signature', sa.Boolean(), nullable=False),
    sa.Column('payload_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('provider', 'event_id')
    )
    op.create_index(op.f('ix_provider_webhook_events_event_id'), 'provider_webhook_events', ['event_id'], unique=False)
    op.create_index(op.f('ix_provider_webhook_events_event_type'), 'provider_webhook_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_provider_webhook_events_provider'), 'provider_webhook_events', ['provider'], unique=False)
    op.create_index(op.f('ix_provider_webhook_events_tenant_id'), 'provider_webhook_events', ['tenant_id'], unique=False)
    op.create_table('sessions',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('csrf_hash', sa.String(length=64), nullable=False),
    sa.Column('ip_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_tenant_id'), 'sessions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_table('tenants',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('lockdown', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=30), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_tenant_id'), 'users', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_tenant_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('tenants')
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_tenant_id'), table_name='sessions')
    op.drop_table('sessions')
    op.drop_index(op.f('ix_provider_webhook_events_tenant_id'), table_name='provider_webhook_events')
    op.drop_index(op.f('ix_provider_webhook_events_provider'), table_name='provider_webhook_events')
    op.drop_index(op.f('ix_provider_webhook_events_event_type'), table_name='provider_webhook_events')
    op.drop_index(op.f('ix_provider_webhook_events_event_id'), table_name='provider_webhook_events')
    op.drop_table('provider_webhook_events')
    op.drop_index(op.f('ix_founder_profiles_user_id'), table_name='founder_profiles')
    op.drop_index(op.f('ix_founder_profiles_tenant_id'), table_name='founder_profiles')
    op.drop_index(op.f('ix_founder_profiles_owner_id'), table_name='founder_profiles')
    op.drop_table('founder_profiles')
    op.drop_index(op.f('ix_execution_tasks_tenant_id'), table_name='execution_tasks')
    op.drop_index(op.f('ix_execution_tasks_business_id'), table_name='execution_tasks')
    op.drop_table('execution_tasks')
    op.drop_index(op.f('ix_execution_receipt_records_trusted'), table_name='execution_receipt_records')
    op.drop_index(op.f('ix_execution_receipt_records_tenant_id'), table_name='execution_receipt_records')
    op.drop_index(op.f('ix_execution_receipt_records_provenance'), table_name='execution_receipt_records')
    op.drop_index(op.f('ix_execution_receipt_records_evidence_type'), table_name='execution_receipt_records')
    op.drop_index(op.f('ix_execution_receipt_records_business_id'), table_name='execution_receipt_records')
    op.drop_index(op.f('ix_execution_receipt_records_action_id'), table_name='execution_receipt_records')
    op.drop_table('execution_receipt_records')
    op.drop_index(op.f('ix_execution_action_records_user_id'), table_name='execution_action_records')
    op.drop_index(op.f('ix_execution_action_records_tenant_id'), table_name='execution_action_records')
    op.drop_index(op.f('ix_execution_action_records_status'), table_name='execution_action_records')
    op.drop_index(op.f('ix_execution_action_records_point_key'), table_name='execution_action_records')
    op.drop_index(op.f('ix_execution_action_records_idempotency_key'), table_name='execution_action_records')
    op.drop_index(op.f('ix_execution_action_records_business_id'), table_name='execution_action_records')
    op.drop_table('execution_action_records')
    op.drop_index(op.f('ix_evidence_tenant_id'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_business_id'), table_name='evidence')
    op.drop_table('evidence')
    op.drop_index(op.f('ix_decisions_tenant_id'), table_name='decisions')
    op.drop_index(op.f('ix_decisions_business_id'), table_name='decisions')
    op.drop_table('decisions')
    op.drop_index(op.f('ix_decision_ledger_tenant_id'), table_name='decision_ledger')
    op.drop_index(op.f('ix_decision_ledger_decision_id'), table_name='decision_ledger')
    op.drop_index(op.f('ix_decision_ledger_business_id'), table_name='decision_ledger')
    op.drop_table('decision_ledger')
    op.drop_index(op.f('ix_community_reports_target_id'), table_name='community_reports')
    op.drop_index(op.f('ix_community_reports_status'), table_name='community_reports')
    op.drop_index(op.f('ix_community_reports_reporter_user_id'), table_name='community_reports')
    op.drop_table('community_reports')
    op.drop_index(op.f('ix_community_replies_user_id'), table_name='community_replies')
    op.drop_index(op.f('ix_community_replies_tenant_id'), table_name='community_replies')
    op.drop_index(op.f('ix_community_replies_post_id'), table_name='community_replies')
    op.drop_index(op.f('ix_community_replies_moderation_status'), table_name='community_replies')
    op.drop_index(op.f('ix_community_replies_deleted'), table_name='community_replies')
    op.drop_table('community_replies')
    op.drop_index(op.f('ix_community_posts_user_id'), table_name='community_posts')
    op.drop_index(op.f('ix_community_posts_tenant_id'), table_name='community_posts')
    op.drop_index(op.f('ix_community_posts_moderation_status'), table_name='community_posts')
    op.drop_index(op.f('ix_community_posts_deleted'), table_name='community_posts')
    op.drop_table('community_posts')
    op.drop_index(op.f('ix_community_blocks_blocker_user_id'), table_name='community_blocks')
    op.drop_index(op.f('ix_community_blocks_blocked_user_id'), table_name='community_blocks')
    op.drop_table('community_blocks')
    op.drop_index(op.f('ix_businesses_tenant_id'), table_name='businesses')
    op.drop_table('businesses')
    op.drop_index(op.f('ix_audit_events_tenant_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_actor_id'), table_name='audit_events')
    op.drop_table('audit_events')
    op.drop_index(op.f('ix_actual_observations_tenant_id'), table_name='actual_observations')
    op.drop_index(op.f('ix_actual_observations_key'), table_name='actual_observations')
    op.drop_index(op.f('ix_actual_observations_business_id'), table_name='actual_observations')
    op.drop_table('actual_observations')
