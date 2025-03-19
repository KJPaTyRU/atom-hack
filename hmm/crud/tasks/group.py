from functools import cache
from typing import TYPE_CHECKING

from hmm.models.tasks.group import TaskGroup
from hmm.crud.base import CRUDBase
from hmm.schemas.tasks.group import (
    TaskGroupCreate,
    TaskGroupFrontCreate,
    TaskGroupFrontRead,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from sqlalchemy.orm import selectinload

from hmm.schemas.tasks.task_groups import Task2GroupCreate

if TYPE_CHECKING:
    from hmm.models.tasks.task_group import Task2Group


@cache
def get_Task2Group() -> type["Task2Group"]:
    from hmm.models.tasks.task_group import Task2Group

    return Task2Group


class TaskGroupCrud(CRUDBase[TaskGroup, TaskGroupFrontRead, TaskGroupCreate]):

    async def create_with_tasks(
        self, session: AsyncSession, data: TaskGroupFrontCreate
    ) -> TaskGroup:
        res = await self.create(session, obj_in=data.to_db())
        t2g = []
        for ti in data.sub_task:
            t2g.append(
                Task2GroupCreate(group_id=res.id, typical_task=ti).model_dump()
            )
        ins_stmt = insert(get_Task2Group()).values(t2g)
        await session.execute(ins_stmt)
        return res


class ExtendedTaskGroupCrud(
    CRUDBase[TaskGroup, TaskGroupFrontRead, TaskGroupCreate]
):

    @property
    def _select_model(self):
        return super()._select_model.options(
            selectinload(self._model.sub_task)
        )


@cache
def get_extended_group_crud():
    return ExtendedTaskGroupCrud()


@cache
def get_group_crud():
    return TaskGroupCrud()
