from pydantic import Field, model_validator
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

    @model_validator(mode="after")
    def val_model(self):
        if (
            (self.hero_lvl == 1 and self.mana > 20)
            or (self.hero_lvl == 1 and self.mana > 50)
            or (self.hero_lvl == 3 and self.mana > 100)
        ):
            raise ValueError(
                f"Too much mana for hero with lvl={self.hero_lvl}. Max mana is"
                " 20 for lvl 1, 50 for lvl 2 and 100 for lvl 3"
            )

        return self


class HeroFrontRead(BaseHeroFields, UuidIdSchemaMixin, CreatedTimeSchemaMixin):
    pass
