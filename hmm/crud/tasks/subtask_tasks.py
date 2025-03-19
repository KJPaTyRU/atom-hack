from functools import cache
from sqlalchemy.ext.asyncio import AsyncSession

from hmm.models.tasks.subtask_tasks import TypicalSubTask
from hmm.crud.base import CRUDBase
from hmm.schemas.tasks.subtask_tasks import (
    TypicalSubTaskCreate,
    TypicalSubTaskFrontRead,
)


class TypicalSubTaskCrud(
    CRUDBase[TypicalSubTask, TypicalSubTaskFrontRead, TypicalSubTaskCreate]
):
    async def bulk_create(
        self, session: AsyncSession, data: list[TypicalSubTaskCreate]
    ):
        db_objs = [self.model(**di.to_db()) for di in data]
        session.add_all(db_objs)
        await session.flush(db_objs)


@cache
def get_typical_task_crud():
    return TypicalSubTaskCrud()
