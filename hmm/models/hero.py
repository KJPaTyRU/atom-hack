from sqlalchemy import String, SmallInteger, Float
from sqlalchemy.orm import Mapped, mapped_column
from hmm.enum import HeroCategory
from hmm.models.base import Base, UUIDDateCreatedMixin, BoundDbModel


class Hero(BoundDbModel, UUIDDateCreatedMixin, Base):
    name: Mapped[str] = mapped_column(String(256))
    hero_class: Mapped[HeroCategory] = mapped_column(
        SmallInteger(), index=True
    )
    hero_lvl: Mapped[int] = mapped_column(SmallInteger(), index=True)

    mana: Mapped[float] = mapped_column(Float(precision=2))

    @classmethod
    def bound_date_column(cls):
        return cls.created_at
