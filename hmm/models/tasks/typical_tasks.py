from functools import cached_property
from sqlalchemy import String, SmallInteger, Float
from sqlalchemy.orm import Mapped, mapped_column
from hmm.enum import TypicalSubTaskType
from hmm.models.base import Base, UUIDDateCreatedMixin, BoundDbModel


class TypicalSubTask(BoundDbModel, UUIDDateCreatedMixin, Base):
    name: Mapped[str] = mapped_column(String(256))

    task_type: Mapped[TypicalSubTaskType] = mapped_column(
        SmallInteger(), index=True
    )
    task_lvl: Mapped[int] = mapped_column(SmallInteger(), index=True)

    w_mana: Mapped[float] = mapped_column(Float(precision=2))
    m_mana: Mapped[float] = mapped_column(Float(precision=2))
    s_mana: Mapped[float] = mapped_column(Float(precision=2))

    @cached_property
    def total_mana(self) -> float:
        return self.w_mana + self.m_mana + self.s_mana

    @classmethod
    def bound_date_column(cls):
        return cls.created_at
