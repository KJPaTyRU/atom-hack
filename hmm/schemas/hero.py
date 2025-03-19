from pydantic import Field
from hmm.enum import HeroCategory
from hmm.schemas.base import (
    CreatedTimeSchemaMixin,
    OrmModel,
    UuidIdSchemaMixin,
)


class BaseHeroFields(OrmModel):
    name: str = Field(min_length=2, max_length=256)
    hero_class: HeroCategory
    hero_lvl: int = Field(le=3, ge=1)
    mana: float = Field(ge=0)


class HeroCreate(BaseHeroFields):
    pass


class HeroFrontRead(BaseHeroFields, UuidIdSchemaMixin, CreatedTimeSchemaMixin):
    pass
