"""Add duration_seconds to run_step_results

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-26

duration_seconds was present in migration 0001 but absent from databases
created before alembic was introduced (via Base.metadata.create_all).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("run_step_results") as batch_op:
        batch_op.add_column(sa.Column("duration_seconds", sa.Float, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("run_step_results") as batch_op:
        batch_op.drop_column("duration_seconds")
