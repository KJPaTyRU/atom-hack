import datetime
from functools import cache
import uuid
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, not_, and_, or_
from hmm.models.timetable import HeroUsedTimeTable
from hmm.crud.base import CRUDBase
from hmm.schemas.timetable import (
    HeroUsedTimeTableCreate,
    HeroUsedTimeTableFrontRead,
)


class HeroUsedTimeTableCrud(
    CRUDBase[
        HeroUsedTimeTable, HeroUsedTimeTableFrontRead, HeroUsedTimeTableCreate
    ]
):

    async def get_banned_heroes(
        self,
        session: AsyncSession,
        date_start: datetime.datetime,
        date_end: datetime.datetime,
    ) -> list[uuid.UUID]:
        stmt = select(HeroUsedTimeTable.hero_id).where(
            # not_(
            or_(
                and_(
                    HeroUsedTimeTable.date_start <= date_start,
                    HeroUsedTimeTable.date_end >= date_start,
                ),
                and_(
                    HeroUsedTimeTable.date_end <= date_end,
                    HeroUsedTimeTable.date_start >= date_end,
                ),
                and_(
                    HeroUsedTimeTable.date_start >= date_start,
                    HeroUsedTimeTable.date_end <= date_end,
                ),
            )
            # )
        )
        return (await session.execute(stmt)).scalars().all()

    async def get_active_heroes(
        self,
        session: AsyncSession,
        date_start: datetime.datetime,
        date_end: datetime.datetime,
    ) -> list[uuid.UUID]:
        stmt = select(HeroUsedTimeTable.hero_id).where(
            not_(
                or_(
                    and_(
                        HeroUsedTimeTable.date_start <= date_start,
                        HeroUsedTimeTable.date_end >= date_start,
                    ),
                    and_(
                        HeroUsedTimeTable.date_end <= date_end,
                        HeroUsedTimeTable.date_start >= date_end,
                    ),
                    and_(
                        HeroUsedTimeTable.date_start >= date_start,
                        HeroUsedTimeTable.date_end <= date_end,
                    ),
                )
            )
        )
        return (await session.execute(stmt)).scalars().all()

    async def set_timetables(
        self,
        session: AsyncSession,
        heroes: list[uuid.UUID],
        expedition_id: uuid.UUID,
        date_start: datetime.datetime,
        date_end: datetime.datetime,
    ):
        data = []
        for hi in heroes:
            data.append(
                HeroUsedTimeTableCreate(
                    hero_id=hi,
                    expedition_id=expedition_id,
                    date_start=date_start,
                    date_end=date_end,
                ).model_dump()
            )
        logger.debug("Added timetables {}", data)
        stmt = insert(HeroUsedTimeTable).values(data)
        await session.execute(stmt)


@cache
def get_timetable_crud():
    return HeroUsedTimeTableCrud()
