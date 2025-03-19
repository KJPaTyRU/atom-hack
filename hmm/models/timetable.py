import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from hmm.models.base import Base, BigIdCreatedDateBaseMixin, BoundDbModel
from hmm.models.expedition import ExpeditionTemplate
from hmm.models.hero import Hero


class HeroUsedTimeTable(BoundDbModel, BigIdCreatedDateBaseMixin, Base):
    hero_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Hero.id, ondelete="CASCADE")
    )
    expedition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(ExpeditionTemplate.id, ondelete="CASCADE")
    )

    date_start: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), index=True
    )
    date_end: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), index=True
    )

    @classmethod
    def bound_date_column(cls):
        return cls.created_at
