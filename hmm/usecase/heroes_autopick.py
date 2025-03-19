import asyncio
from functools import cache
from typing import Callable
import uuid

from loguru import logger

from hmm.core.db import AsyncSessionMaker
from hmm.crud.expedition import get_expedition_template_crud
from hmm.crud.hero import get_hero_crud
from hmm.enum import ExpeditionStatus
from hmm.usecase.services.heroes_autopick.my_greedy import (
    PickResult,
    assign_heroes,
)


class HeroesAutoPickUseCase:

    def __init__(self, calc_func: Callable = assign_heroes):
        self.calc_func = calc_func

    async def process(self, expedition_id: uuid.UUID):
        exp_crud = get_expedition_template_crud()
        async with AsyncSessionMaker() as session:
            try:
                tasks = await exp_crud.get_subtasks(session, expedition_id)
                heroes = await get_hero_crud().get_multi(session)
                selected_heroes: PickResult = await asyncio.to_thread(
                    self.calc_func, tasks, heroes
                )
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
                        total_mana=selected_heroes.manas.s_mana
                        + selected_heroes.manas.w_mana
                        + selected_heroes.manas.m_mana,
                    ),
                )
            except Exception as e:
                logger.exception(e)
                await exp_crud.set_status(
                    session, expedition_id, ExpeditionStatus.error
                )
            await session.commit()


@cache
def get_hap_usecase() -> HeroesAutoPickUseCase:
    return HeroesAutoPickUseCase()
