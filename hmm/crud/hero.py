from functools import cache

from hmm.models.hero import Hero
from hmm.crud.base import CRUDBase
from hmm.schemas.hero import HeroCreate, HeroFrontRead


class HeroCrud(CRUDBase[Hero, HeroFrontRead, HeroCreate]):
    pass


@cache
def get_hero_crud():
    return HeroCrud()
