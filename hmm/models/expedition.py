import datetime
from functools import cache
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import String, Text, ForeignKey, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from hmm.models.base import (
    Base,
    UUIDDateCreatedMixin,
    DateCreatedMixin,
    BoundDbModel,
)
from hmm.models.tasks.group import TaskGroup

if TYPE_CHECKING:
    from hmm.models.hero import Hero


@cache
def get_Hero() -> type["Hero"]:
    from hmm.models.hero import Hero

    return Hero


class ExpeditionTemplate(BoundDbModel, UUIDDateCreatedMixin, Base):
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text())

    tasks: Mapped[list[TaskGroup]] = ...

    @classmethod
    def bound_date_column(cls):
        return cls.created_at


class Chronicles(BoundDbModel, UUIDDateCreatedMixin, Base):
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text())

    date_start: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), server_default=func.now()
    )
    date_end: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), server_default=func.now()
    )

    expedition_template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(ExpeditionTemplate.id, ondelete="CASCADE"), index=True
    )

    # author_id: Mapped[int] = ...

    # Relationship
    expedition: Mapped[ExpeditionTemplate] = relationship(ExpeditionTemplate)
    heroies: Mapped[list["Hero"]] = ...

    @classmethod
    def bound_date_column(cls):
        return cls.created_at


class Heroes2Chronicles(BoundDbModel, DateCreatedMixin, Base):
    hero_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(get_Hero().id, ondelete="CASCADE"), primary_key=True
    )
    chronicle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Chronicles.id, ondelete="CASCADE"), primary_key=True
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
    "TaskGroup",
    secondary=Task2Expedition.__tablename__,
    # secondaryjoin=Task2Expedition.expedition_id == ExpeditionTemplate.id,
    uselist=True,
)


Chronicles.heroies = relationship(
    "Hero",
    secondary=Heroes2Chronicles.__tablename__,
    # secondaryjoin=Heroes2Chronicles.chronicle_id == Chronicles.id,
    uselist=True,
)
