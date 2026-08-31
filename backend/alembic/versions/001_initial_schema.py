"""Initial schema — all PANAGAH tables

Revision ID: 001_initial
Revises:
Create Date: 2026-08-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Projects
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.String(50), nullable=False, server_default="0.1.0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Sites
    op.create_table(
        "sites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Materials
    op.create_table(
        "materials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("material_type", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Float, nullable=False, server_default="0"),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("unit_cost", sa.Float, nullable=True),
        sa.Column("cost_unit", sa.String(50), nullable=True),
        sa.Column("locally_available", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Constraint Sets
    op.create_table(
        "constraint_sets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("schema_version", sa.String(50), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Design Candidates
    op.create_table(
        "design_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Design Versions
    op.create_table(
        "design_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Validation Runs
    op.create_table(
        "validation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("design_version_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("verdict", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Reviews
    op.create_table(
        "reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("design_version_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("decision", sa.String(50), nullable=True),
        sa.Column("comments", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Audit Events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(255), nullable=True),
        sa.Column("metadata", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Users (for authentication)
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="engineer"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("audit_events")
    op.drop_table("reviews")
    op.drop_table("validation_runs")
    op.drop_table("design_versions")
    op.drop_table("design_candidates")
    op.drop_table("constraint_sets")
    op.drop_table("materials")
    op.drop_table("sites")
    op.drop_table("projects")
