import sys
import uuid

from loguru import logger

sys.path.append("/home/king/mephi/atom-hack/")

from hmm.core.types import ManaFloatType
from hmm.schemas.base import OrmModel

from collections import defaultdict
from hmm.enum import HeroCategory
from hmm.schemas.hero import HeroFrontRead
from hmm.schemas.tasks.subtask_tasks import TypicalSubTaskFrontRead


class Manas(OrmModel):
    w_mana: ManaFloatType = 0
    m_mana: ManaFloatType = 0
    s_mana: ManaFloatType = 0


class THeroe(OrmModel):
    id_: uuid.UUID
    ts: float = 0
    tabs: float = 0
    v: float = 0


class PickResult(OrmModel):
    heroes: list[uuid.UUID]
    manas: Manas


def group_by_class(heroes: list[HeroFrontRead], field: str):
    res = defaultdict(list)
    for hi in heroes:
        res[getattr(hi, field)].append(hi)
    return res


def count_mana(tasks: list[TypicalSubTaskFrontRead]) -> Manas:
    manas = Manas()
    for ti in tasks:
        manas.w_mana += ti.w_mana
        manas.m_mana += ti.m_mana
        manas.s_mana += ti.s_mana
    return manas


def pick_heroes(
    requested_mana: float, heroes: list[HeroFrontRead]
) -> list[uuid.UUID]:
    _tdict: dict[uuid.UUID, THeroe] = dict()
    for hi in heroes:
        ts = hi.mana - requested_mana
        tabs = abs(ts)
        _tdict[hi.id] = THeroe(ts=ts, tabs=tabs, id_=hi.id, v=hi.mana)
    rmt = requested_mana
    res = []
    ttlist = list(_tdict.values())
    while rmt > 0 and ttlist:
        ttlist = sorted(ttlist, key=lambda x: (x.tabs, x.ts), reverse=True)
        kd = ttlist.pop()
        res.append(kd.id_)
        rmt -= kd.v
        if rmt <= 0:
            break
        for si in ttlist:
            si.ts = si.v - rmt
            si.tabs = abs(si.ts)
    if rmt <= 0:
        return res
    return []


def assign_heroes(
    tasks: list[TypicalSubTaskFrontRead], heroes: list[HeroFrontRead]
):
    gheroes = group_by_class(heroes, "hero_class")
    manas = count_mana(tasks)
    logger.debug("manas={}", manas)
    w_heroes, m_heroes, s_heroes = [], [], []

    if manas.w_mana > 0:
        w_heroes = pick_heroes(manas.w_mana, gheroes[HeroCategory.warrior])
        if not w_heroes:
            return PickResult(heroes=[], manas=manas)

    if manas.m_mana > 0:
        m_heroes = pick_heroes(manas.m_mana, gheroes[HeroCategory.magician])

        if not m_heroes:
            return PickResult(heroes=[], manas=manas)

    if manas.s_mana > 0:
        s_heroes = pick_heroes(manas.s_mana, gheroes[HeroCategory.strategist])
        if not s_heroes:
            return PickResult(heroes=[], manas=manas)
    return PickResult(heroes=w_heroes + m_heroes + s_heroes, manas=manas)


def test():
    # Пример входных данных
    _tasks = [
        {
            "created_at": "2025-03-19T19:42:49.728146Z",
            "id": "f1434cdd-9305-4329-9d66-bce442242a7c",
            "name": "[F] Интеграция магии и боя",
            "task_type": 2,
            "task_lvl": 3,
            "w_mana": 3,
            "m_mana": 8,
            "s_mana": 4,
        },
        {
            "created_at": "2025-03-19T19:42:49.728146Z",
            "id": "dcc0531e-8416-438e-af31-55812e4f0d27",
            "name": "[М] Разработка боевых заклинаний стихий",
            "task_type": 1,
            "task_lvl": 1,
            "w_mana": 0,
            "m_mana": 3,
            "s_mana": 8,
        },
        #   {
        #     "created_at": "2025-03-19T19:42:49.728146Z",
        #     "id": "7ec723a5-0dc9-4df2-aaa0-49c408fbe1d1",
        #     "name": "[М] Разработка боевых заклинаний стихий",
        #     "task_type": 1,
        #     "task_lvl": 2,
        #     "w_mana": 0,
        #     "m_mana": 5,
        #     "s_mana": 16
        #   },
        #   {
        #     "created_at": "2025-03-19T19:42:49.728146Z",
        #     "id": "473656e1-b726-44b8-bde4-4fbad45dbfdb",
        #     "name": "[М] Разработка боевых заклинаний стихий",
        #     "task_type": 1,
        #     "task_lvl": 3,
        #     "w_mana": 0,
        #     "m_mana": 12,
        #     "s_mana": 32
        #   },
        #   {
        #     "created_at": "2025-03-19T19:42:49.728146Z",
        #     "id": "243f3645-8f4c-4b2a-b94a-375a81f61ef6",
        #     "name": "[М] Разработка защитных чар",
        #     "task_type": 2,
        #     "task_lvl": 1,
        #     "w_mana": 0,
        #     "m_mana": 1,
        #     "s_mana": 2
        #   },
        #   {
        #     "created_at": "2025-03-19T19:42:49.728146Z",
        #     "id": "44ee330d-9b50-4a3a-b9b3-ac8fe05db81d",
        #     "name": "[М] Разработка защитных чар",
        #     "task_type": 2,
        #     "task_lvl": 2,
        #     "w_mana": 0,
        #     "m_mana": 3,
        #     "s_mana": 7
        #   },
        #   {
        #     "created_at": "2025-03-19T19:42:49.728146Z",
        #     "id": "9435643c-90fb-4f57-95f0-46de43a5371d",
        #     "name": "[М] Разработка защитных чар",
        #     "task_type": 2,
        #     "task_lvl": 3,
        #     "w_mana": 0,
        #     "m_mana": 5,
        #     "s_mana": 14
        #   },
    ]
    tasks = [TypicalSubTaskFrontRead.model_validate(ti) for ti in _tasks]
    _heroes = [
        {
            "created_at": "2025-03-19T20:36:43.335852Z",
            "id": "85be241b-2a23-4a9a-80ce-c4b413449e13",
            "name": "31",
            "hero_class": 1,
            "hero_lvl": 1,
            "mana": 13,
        },
        {
            "created_at": "2025-03-19T20:36:38.724308Z",
            "id": "9260ca72-8c26-4511-b301-748693622e89",
            "name": "32",
            "hero_class": 2,
            "hero_lvl": 1,
            "mana": 13,
        },
        {
            "created_at": "2025-03-19T20:36:34.281727Z",
            "id": "1c554720-043c-4385-a794-5cd9b2ee9517",
            "name": "33",
            "hero_class": 3,
            "hero_lvl": 1,
            "mana": 13,
        },
        {
            "created_at": "2025-03-19T20:36:27.445741Z",
            "id": "662fb201-8954-4dae-9ba8-1a656ba365a5",
            "name": "23",
            "hero_class": 3,
            "hero_lvl": 1,
            "mana": 10,
        },
        {
            "created_at": "2025-03-19T20:36:22.233277Z",
            "id": "2ad80d72-356d-472a-83c3-83127e7dd0a3",
            "name": "22",
            "hero_class": 2,
            "hero_lvl": 1,
            "mana": 10,
        },
        {
            "created_at": "2025-03-19T20:36:17.934340Z",
            "id": "63976caf-1a5e-4582-96e5-79aac5449c0f",
            "name": "21",
            "hero_class": 1,
            "hero_lvl": 1,
            "mana": 10,
        },
        {
            "created_at": "2025-03-19T20:36:05.170270Z",
            "id": "47b0c694-18fb-488a-afba-fbc10fe63904",
            "name": "13",
            "hero_class": 3,
            "hero_lvl": 1,
            "mana": 5,
        },
        {
            "created_at": "2025-03-19T20:36:00.269412Z",
            "id": "649ad4c9-e251-4e35-b8e4-ba1fec4dce61",
            "name": "12",
            "hero_class": 2,
            "hero_lvl": 1,
            "mana": 5,
        },
        {
            "created_at": "2025-03-19T20:35:55.671254Z",
            "id": "0e037faa-6b10-4f8c-8cf4-921d1b39d761",
            "name": "11",
            "hero_class": 1,
            "hero_lvl": 1,
            "mana": 5,
        },
    ]

    tasks = [TypicalSubTaskFrontRead.model_validate(ti) for ti in _tasks]
    heroes = [HeroFrontRead.model_validate(ti) for ti in _heroes]

    result = assign_heroes(tasks, heroes)
    if not result:
        print("Группа не может быть сформирована")
    else:
        print("Герои, отправленные в экспедицию:")
        print(tasks)
        hd = {hi.id: hi for hi in heroes}
        shd = [hd[hi] for hi in result if hi in hd]
        st = "\n\n".join(map(str, shd))
        print(f"\nHeroes:{st}")


if __name__ == "__main__":
    test()
