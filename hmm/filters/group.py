from datetime import datetime

from hmm.core.filtering.sqlalchemy import Filter
from hmm.models.tasks.group import TaskGroup


class TaskGroupFilter(Filter):
    created_at__from: datetime | None = None
    created_at__till: datetime | None = None

    name__ilike: str | None = None

    class Constants(Filter.Constants):
        model = TaskGroup
        search_model_fields = ["created_at", "name"]
