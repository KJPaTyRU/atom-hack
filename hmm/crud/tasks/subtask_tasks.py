from functools import cache

from hmm.models.tasks.subtask_tasks import TypicalSubTask
from hmm.crud.base import CRUDBase
from hmm.schemas.tasks.subtask_tasks import (
    TypicalSubTaskCreate,
    TypicalSubTaskFrontRead,
)


class TypicalSubTaskCrud(
    CRUDBase[TypicalSubTask, TypicalSubTaskFrontRead, TypicalSubTaskCreate]
):
    pass


@cache
def get_typical_task_crud():
    return TypicalSubTaskCrud()
