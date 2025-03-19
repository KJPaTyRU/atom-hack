import datetime
from sqlalchemy import Boolean, DateTime, String, Text, false, func, true
from sqlalchemy.orm import Mapped, mapped_column
from hmm.models.base import Base, BigIdCreatedDateBaseMixin, BoundDbModel
from hmm.schemas.auth import UserNameStr


class User(BoundDbModel, BigIdCreatedDateBaseMixin, Base):
    username: Mapped[UserNameStr] = mapped_column(
        String(64), index=True, unique=True
    )
    hashed_password: Mapped[str] = mapped_column(Text(), nullable=False)

    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), server_default=func.now()
    )
    is_super: Mapped[bool] = mapped_column(Boolean(), server_default=false())
    is_active: Mapped[bool] = mapped_column(Boolean(), server_default=true())

    @classmethod
    def bound_date_column(cls):
        return cls.created_at
