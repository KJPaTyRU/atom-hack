import asyncio
import datetime
from functools import cache
from typing import Callable
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from hmm.core.db import AsyncSessionMaker
from hmm.crud.expedition import get_expedition_template_crud
from hmm.crud.hero import get_hero_crud
from hmm.crud.timetable import get_timetable_crud
from hmm.enum import ExpeditionStatus
from hmm.models.hero import Hero
from hmm.models.tasks.subtask_tasks import TypicalSubTask
from hmm.usecase.services.heroes_autopick.my_greedy import (
    ExpHeroe,
    PickResult,
    assign_heroes,
)

# Koef calculator


class ManaKoefs:
    h2e_k_mapper = {
        # 1: {1: 1, 2: 1.6, 3: 2.3},
        # 2: {1: 0.89, 2: 1, 3: 1.8},
        # 3: {1: 0.6, 2: 0.8, 3: 1},
        1: {1: 1, 2: 1 / 1.6, 3: 1 / 2.3},
        2: {1: 1 / 0.89, 2: 1, 3: 1 / 1.8},
        3: {1: 1 / 0.6, 2: 1 / 0.8, 3: 1},
    }

    def calc_mean_lvl(self, tasks: list[TypicalSubTask]) -> float:
        if len(tasks) == 0:
            raise ValueError("0 tasks found in expedition!")
        ec = 0
        for ti in tasks:
            ec += ti.task_lvl
        return ec / len(tasks)

    def koef_calculator(self, h_lvl: int, e_lvl_mean: float) -> float:
        def hero_check(e_lvl_type: int):
            return self.h2e_k_mapper[h_lvl][e_lvl_type]

        result_k = 1
        if e_lvl_mean <= 1.5:
            # simple exp
            result_k = hero_check(1)
        elif e_lvl_mean <= 2.5:
            # med exp
            result_k = hero_check(2)
        else:
            # had exp
            result_k = hero_check(3)
        return result_k


async def get_free_heroes(
    session: AsyncSession,
    date_start: datetime.datetime,
    date_end: datetime.datetime,
):
    h_ids = await get_timetable_crud().get_banned_heroes(
        session, date_start, date_end
    )
    logger.debug("h_ids={}", h_ids)
    return await get_hero_crud().get_multi(
        session, operator_expressions=[Hero.id.not_in(h_ids)]
    )


class HeroesAutoPickUseCase:

    def __init__(
        self, calc_func: Callable = assign_heroes, mk: ManaKoefs = ManaKoefs()
    ):
        self.calc_func = calc_func
        self.mk = mk

    async def process(self, expedition_id: uuid.UUID):
        exp_crud = get_expedition_template_crud()
        async with AsyncSessionMaker() as session:
            try:
                expedition = await exp_crud.get_one_raw(
                    session, id=expedition_id
                )
                tasks = await exp_crud.get_subtasks(session, expedition_id)
                heroes = await get_free_heroes(
                    session, expedition.date_start, expedition.date_end
                )

                mean_exp_lvl = self.mk.calc_mean_lvl(tasks)

                if not heroes:
                    raise ValueError()
                selected_heroes: PickResult = await asyncio.to_thread(
                    self.calc_func,
                    tasks,
                    [
                        ExpHeroe(
                            hero=hi,
                            exp_k=self.mk.koef_calculator(
                                hi.hero_lvl, mean_exp_lvl
                            ),
                        )
                        for hi in heroes
                    ],
                )
                if not selected_heroes.heroes:
                    raise ValueError()
                await exp_crud.insert_heroes(
                    session, selected_heroes.heroes, expedition_id
                )

                await exp_crud.update(
                    session,
                    update_filter=dict(id=expedition_id),
                    update_values=dict(
                        status=ExpeditionStatus.finished,
                        w_mana=selected_heroes.manas.w_mana,
                        m_mana=selected_heroes.manas.m_mana,
                        s_mana=selected_heroes.manas.s_mana,
                        mean_exp_lvl=mean_exp_lvl,
                        total_mana=selected_heroes.manas.s_mana
                        + selected_heroes.manas.w_mana
                        + selected_heroes.manas.m_mana,
                    ),
                )
                await get_timetable_crud().set_timetables(
                    session,
                    selected_heroes.heroes,
                    expedition_id,
                    expedition.date_start,
                    expedition.date_end,
                )
                await session.commit()
            except Exception as e:
                logger.exception(e)
                async with AsyncSessionMaker() as session2:

                    await exp_crud.set_status(
                        session2, expedition_id, ExpeditionStatus.error
                    )
                    await session2.commit()


@cache
def get_hap_usecase() -> HeroesAutoPickUseCase:
    return HeroesAutoPickUseCase()
