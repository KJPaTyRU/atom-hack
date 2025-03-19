from datetime import datetime

from hmm.core.filtering.sqlalchemy import Filter
from hmm.models.expedition import ExpeditionTemplate


class ExpeditionTemplateFilter(Filter):
    created_at__from: datetime | None = None
    created_at__till: datetime | None = None

    name__ilike: str | None = None
    description__ilike: str | None = None

    date_start__from: datetime | None = None
    date_start__till: datetime | None = None

    date_end__from: datetime | None = None
    date_end__till: datetime | None = None

    class Constants(Filter.Constants):
        model = ExpeditionTemplate
        search_model_fields = [
            "created_at",
            "name",
            "description",
            "date_start",
            "date_end",
        ]
