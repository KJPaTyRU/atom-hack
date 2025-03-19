from datetime import datetime

from hmm.core.filtering.sqlalchemy import Filter
from hmm.enum import SubTaskType
from hmm.models.tasks.subtask_tasks import TypicalSubTask


class TypicalSubTaskFilter(Filter):
    created_at__from: datetime | None = None
    created_at__till: datetime | None = None

    name__ilike: str | None = None
    task_type: SubTaskType | None = None
    task_lvl: int | None = None
    w_mana__gte: float | None = None
    m_mana__gte: float | None = None
    s_mana__gte: float | None = None

    w_mana__lte: float | None = None
    m_mana__lte: float | None = None
    s_mana__lte: float | None = None

    class Constants(Filter.Constants):
        model = TypicalSubTask
        search_model_fields = [
            "created_at",
            "w_mana",
            "m_mana",
            "s_mana",
            "name",
            "task_lvl",
            "task_type",
        ]
