"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), server_default='teacher'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'groups',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(20), unique=True, index=True, nullable=False),
        sa.Column('owner_id', UUID, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'students',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('group_id', UUID, sa.ForeignKey('groups.id'), nullable=False),
        sa.Column('cf_handle', sa.String(100), index=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('joined_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'submissions',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('student_id', UUID, sa.ForeignKey('students.id'), index=True, nullable=False),
        sa.Column('cf_submission_id', sa.Integer, unique=True, nullable=False),
        sa.Column('problem_id', sa.String(20), nullable=False),
        sa.Column('problem_name', sa.String(255), nullable=False),
        sa.Column('language', sa.String(50), nullable=False),
        sa.Column('verdict', sa.String(50), nullable=False),
        sa.Column('source_code', sa.Text, nullable=False),
        sa.Column('submitted_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'style_profiles',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('student_id', UUID, sa.ForeignKey('students.id'), unique=True, nullable=False),
        sa.Column('profile_data', JSONB, nullable=False),
        sa.Column('submission_count', sa.Integer, server_default='0'),
        sa.Column('last_updated', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'analysis_results',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('submission_id', UUID, sa.ForeignKey('submissions.id'), unique=True, nullable=False),
        sa.Column('student_id', UUID, sa.ForeignKey('students.id'), index=True, nullable=False),
        sa.Column('anomaly_score', sa.Float, nullable=False),
        sa.Column('ai_score', sa.Float, server_default='0.0'),
        sa.Column('feature_deviations', JSONB, nullable=False),
        sa.Column('cross_matches', JSONB, nullable=True),
        sa.Column('verdict', sa.String(50), nullable=False),
        sa.Column('confidence', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('analysis_results')
    op.drop_table('style_profiles')
    op.drop_table('submissions')
    op.drop_table('students')
    op.drop_table('groups')
    op.drop_table('users')
