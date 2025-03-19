"""Remove journal

Revision ID: 264d0b737d17
Revises: eeb44c191c6e
Create Date: 2025-03-19 21:18:15.666264

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "264d0b737d17"
down_revision: Union[str, None] = "eeb44c191c6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "hmm_heroes2_expedition",
        sa.Column("hero_id", sa.Uuid(), nullable=False),
        sa.Column("expedition_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["expedition_id"],
            ["hmm_expedition_template.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["hero_id"], ["hmm_hero.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("hero_id", "expedition_id"),
    )
    op.drop_index(
        "ix_hmm_chronicles_expedition_template_id", table_name="hmm_chronicles"
    )
    op.drop_table("hmm_heroes2_chronicles")
    op.drop_table("hmm_chronicles")
    op.add_column(
        "hmm_expedition_template",
        sa.Column(
            "date_start",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "hmm_expedition_template",
        sa.Column(
            "date_end",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "hmm_expedition_template",
        sa.Column(
            "status", sa.SmallInteger(), server_default="1", nullable=False
        ),
    )
    op.add_column(
        "hmm_expedition_template",
        sa.Column(
            "w_mana", sa.Float(precision=2), server_default="0", nullable=False
        ),
    )
    op.add_column(
        "hmm_expedition_template",
        sa.Column(
            "m_mana", sa.Float(precision=2), server_default="0", nullable=False
        ),
    )
    op.add_column(
        "hmm_expedition_template",
        sa.Column(
            "s_mana", sa.Float(precision=2), server_default="0", nullable=False
        ),
    )
    op.add_column(
        "hmm_expedition_template",
        sa.Column(
            "total_mana",
            sa.Float(precision=2),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "hmm_expedition_template",
        sa.Column("author_id", sa.BigInteger(), nullable=False),
    )
    op.create_index(
        op.f("ix_hmm_expedition_template_author_id"),
        "hmm_expedition_template",
        ["author_id"],
        unique=False,
    )
    op.create_foreign_key(
        None,
        "hmm_expedition_template",
        "hmm_user",
        ["author_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column(
        "hmm_hero",
        "mana",
        existing_type=sa.REAL(),
        type_=sa.Float(precision=2),
        existing_nullable=False,
    )
    op.alter_column(
        "hmm_typical_sub_task",
        "w_mana",
        existing_type=sa.REAL(),
        type_=sa.Float(precision=2),
        existing_nullable=False,
    )
    op.alter_column(
        "hmm_typical_sub_task",
        "m_mana",
        existing_type=sa.REAL(),
        type_=sa.Float(precision=2),
        existing_nullable=False,
    )
    op.alter_column(
        "hmm_typical_sub_task",
        "s_mana",
        existing_type=sa.REAL(),
        type_=sa.Float(precision=2),
        existing_nullable=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "hmm_typical_sub_task",
        "s_mana",
        existing_type=sa.Float(precision=2),
        type_=sa.REAL(),
        existing_nullable=False,
    )
    op.alter_column(
        "hmm_typical_sub_task",
        "m_mana",
        existing_type=sa.Float(precision=2),
        type_=sa.REAL(),
        existing_nullable=False,
    )
    op.alter_column(
        "hmm_typical_sub_task",
        "w_mana",
        existing_type=sa.Float(precision=2),
        type_=sa.REAL(),
        existing_nullable=False,
    )
    op.alter_column(
        "hmm_hero",
        "mana",
        existing_type=sa.Float(precision=2),
        type_=sa.REAL(),
        existing_nullable=False,
    )
    op.drop_constraint(None, "hmm_expedition_template", type_="foreignkey")
    op.drop_index(
        op.f("ix_hmm_expedition_template_author_id"),
        table_name="hmm_expedition_template",
    )
    op.drop_column("hmm_expedition_template", "author_id")
    op.drop_column("hmm_expedition_template", "total_mana")
    op.drop_column("hmm_expedition_template", "s_mana")
    op.drop_column("hmm_expedition_template", "m_mana")
    op.drop_column("hmm_expedition_template", "w_mana")
    op.drop_column("hmm_expedition_template", "status")
    op.drop_column("hmm_expedition_template", "date_end")
    op.drop_column("hmm_expedition_template", "date_start")
    op.create_table(
        "hmm_heroes2_chronicles",
        sa.Column("hero_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "chronicle_id", sa.UUID(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chronicle_id"],
            ["hmm_chronicles.id"],
            name="hmm_heroes2_chronicles_chronicle_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["hero_id"],
            ["hmm_hero.id"],
            name="hmm_heroes2_chronicles_hero_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "hero_id", "chronicle_id", name="hmm_heroes2_chronicles_pkey"
        ),
    )
    op.create_table(
        "hmm_chronicles",
        sa.Column(
            "name", sa.VARCHAR(length=256), autoincrement=False, nullable=False
        ),
        sa.Column(
            "description", sa.TEXT(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "date_start",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "date_end",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "expedition_template_id",
            sa.UUID(),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["expedition_template_id"],
            ["hmm_expedition_template.id"],
            name="hmm_chronicles_expedition_template_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="hmm_chronicles_pkey"),
    )
    op.create_index(
        "ix_hmm_chronicles_expedition_template_id",
        "hmm_chronicles",
        ["expedition_template_id"],
        unique=False,
    )
    op.drop_table("hmm_heroes2_expedition")
    # ### end Alembic commands ###
