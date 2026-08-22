"""Simli slot leases: reserve a video slot when the token is issued.

Revision ID: e6f7a8b9c0d1
Revises: c6d7e8f9a0b1
Create Date: 2026-08-22

The capacity gate used to count speaking sessions, but the browser asks for a
video token before its session exists, so a simultaneous start let every
candidate through. A lease records the claim at the moment it is granted.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, None] = "c6d7e8f9a0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "simli_slot_leases"


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = :t"),
        {"t": name},
    )
    return rows.first() is not None


def _has_index(name: str) -> bool:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :n"),
        {"n": name},
    )
    return rows.first() is not None


def upgrade() -> None:
    if not _has_table(TABLE):
        op.create_table(
            TABLE,
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "actor",
                sa.String(length=255),
                nullable=False,
            ),
            sa.Column(
                "expires_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    # One lease per candidate, so a page reload renews the claim instead of
    # consuming a second slot. The upsert in the service relies on this.
    if not _has_index("uq_simli_slot_leases_actor"):
        op.create_index(
            "uq_simli_slot_leases_actor",
            TABLE,
            ["actor"],
            unique=True,
        )
    if not _has_index("ix_simli_slot_leases_expires_at"):
        op.create_index(
            "ix_simli_slot_leases_expires_at",
            TABLE,
            ["expires_at"],
        )


def downgrade() -> None:
    if _has_index("ix_simli_slot_leases_expires_at"):
        op.drop_index("ix_simli_slot_leases_expires_at", table_name=TABLE)
    if _has_index("uq_simli_slot_leases_actor"):
        op.drop_index("uq_simli_slot_leases_actor", table_name=TABLE)
    if _has_table(TABLE):
        op.drop_table(TABLE)
