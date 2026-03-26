"""Add input_row_count, input_column_count, duration_seconds to report_runs

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-26

These columns exist in the ORM model and migration 0001 but were absent from
databases created before alembic was introduced (via Base.metadata.create_all).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("report_runs") as batch_op:
        batch_op.add_column(sa.Column("input_row_count", sa.Integer, nullable=True))
        batch_op.add_column(sa.Column("input_column_count", sa.Integer, nullable=True))
        batch_op.add_column(sa.Column("duration_seconds", sa.Float, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("report_runs") as batch_op:
        batch_op.drop_column("duration_seconds")
        batch_op.drop_column("input_column_count")
        batch_op.drop_column("input_row_count")
