from datetime import datetime

from hmm.core.filtering.sqlalchemy import Filter
from hmm.enum import HeroCategory
from hmm.models.hero import Hero


class HeroFilter(Filter):
    created_at__from: datetime | None = None
    created_at__till: datetime | None = None

    name__ilike: str | None = None
    hero_class: HeroCategory | None = None
    hero_lvl: int | None = None
    mana__gte: float | None = None
    mana__lte: float | None = None

    class Constants(Filter.Constants):
        model = Hero
        search_model_fields = [
            "created_at",
            "name",
            "hero_lvl",
            "hero_class",
            "mana",
        ]
