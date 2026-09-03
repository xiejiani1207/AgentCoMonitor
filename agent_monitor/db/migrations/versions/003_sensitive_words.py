"""add sensitive_words table

Revision ID: 003
Revises: 002
Create Date: 2026-08-30
"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

# 初始敏感词（与旧硬编码黑名单一致，带分类）
_DEFAULT_SENSITIVE_WORDS = [
    ("保证收益", "收益承诺"),
    ("稳赚", "收益承诺"),
    ("绝不亏损", "收益承诺"),
    ("肯定会上涨", "收益承诺"),
    ("包赚", "收益承诺"),
    ("保本", "收益承诺"),
    ("无风险", "风险误导"),
    ("零风险", "风险误导"),
    ("必然", "绝对化用语"),
    ("绝对", "绝对化用语"),
]


def upgrade() -> None:
    table = op.create_table(
        "sensitive_words",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("word", sa.String(64), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("word"),
    )
    # 初始化默认敏感词
    op.bulk_insert(
        table,
        [
            {"word": word, "category": category, "created_at": datetime.utcnow()}
            for word, category in _DEFAULT_SENSITIVE_WORDS
        ],
    )


def downgrade() -> None:
    op.drop_table("sensitive_words")
