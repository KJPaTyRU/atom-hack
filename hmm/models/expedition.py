import datetime
from functools import cache
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    func,
    DateTime,
    SmallInteger,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from hmm.enum import ExpeditionStatus
from hmm.models.base import (
    Base,
    UUIDDateCreatedMixin,
    DateCreatedMixin,
    BoundDbModel,
)
from hmm.models.tasks.group import TaskGroup

if TYPE_CHECKING:
    from hmm.models.hero import Hero
    from hmm.models.auth import User


@cache
def get_Hero() -> type["Hero"]:
    from hmm.models.hero import Hero

    return Hero


@cache
def get_User() -> type["User"]:
    from hmm.models.auth import User

    return User


class ExpeditionTemplate(BoundDbModel, UUIDDateCreatedMixin, Base):
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text())

    date_start: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), server_default=func.now()
    )
    date_end: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), server_default=func.now()
    )
    status: Mapped[ExpeditionStatus] = mapped_column(
        SmallInteger(), server_default=str(ExpeditionStatus.created.value)
    )

    w_mana: Mapped[float] = mapped_column(
        Float(precision=2), server_default="0"
    )
    m_mana: Mapped[float] = mapped_column(
        Float(precision=2), server_default="0"
    )
    s_mana: Mapped[float] = mapped_column(
        Float(precision=2), server_default="0"
    )
    total_mana: Mapped[float] = mapped_column(
        Float(precision=2), server_default="0"
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey(get_User().id, ondelete="CASCADE"), index=True
    )

    tasks: Mapped[list[TaskGroup]] = ...
    heroes: Mapped[list["Hero"]] = ...
    author: Mapped["User"] = relationship(get_User())

    @classmethod
    def bound_date_column(cls):
        return cls.created_at


class Heroes2Expedition(BoundDbModel, DateCreatedMixin, Base):
    hero_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(get_Hero().id, ondelete="CASCADE"), primary_key=True
    )
    expedition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(ExpeditionTemplate.id, ondelete="CASCADE"), primary_key=True
    )


class Task2Expedition(BoundDbModel, DateCreatedMixin, Base):
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(TaskGroup.id, ondelete="CASCADE"), primary_key=True
    )
    expedition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(ExpeditionTemplate.id, ondelete="CASCADE"), primary_key=True
    )

    @classmethod
    def bound_date_column(cls):
        return cls.created_at


ExpeditionTemplate.tasks = relationship(
    "TaskGroup", secondary=Task2Expedition.__tablename__, uselist=True
)


ExpeditionTemplate.heroes = relationship(
    "Hero", secondary=Heroes2Expedition.__tablename__, uselist=True
)
