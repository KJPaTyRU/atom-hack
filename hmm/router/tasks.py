from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from hmm.core.auth.auth import authenticate_user
from hmm.core.db import get_session
from hmm.core.filtering.base import FilterDepends
from hmm.core.ordering import OrderDepends, Ordering
from hmm.core.paginator import Paginator, paginator100
from hmm.crud.tasks.group import (
    ExtendedTaskGroupCrud,
    TaskGroupCrud,
    get_extended_group_crud,
    get_group_crud,
)
from hmm.crud.tasks.subtask_tasks import (
    TypicalSubTaskCrud,
    get_typical_task_crud,
)
from hmm.filters.group import TaskGroupFilter
from hmm.filters.subtask_tasks import TypicalSubTaskFilter
from hmm.models.tasks.group import TaskGroup
from hmm.models.tasks.subtask_tasks import TypicalSubTask
from hmm.router.base import base_model_get
from hmm.schemas.tasks.group import TaskGroupFrontCreate, TaskGroupFrontRead
from hmm.schemas.tasks.subtask_tasks import (
    TypicalSubTaskCreate,
    TypicalSubTaskFrontRead,
)
from hmm.usecase.services.grimuar_extractors.csv import CSVGrimuarExtractor

router = APIRouter(
    prefix="/tasks", dependencies=[Depends(authenticate_user)], tags=["Tasks"]
)


def get_router() -> APIRouter:
    return router


# sub-task
@router.get("/sub-task")
async def get_sub_task(
    response: Response,
    session: AsyncSession = Depends(get_session),
    crud: TypicalSubTaskCrud = Depends(get_typical_task_crud),
    pagination: Paginator = Depends(paginator100),
    query_filter: TypicalSubTaskFilter = FilterDepends(TypicalSubTaskFilter),
    ordering: Ordering = OrderDepends(Ordering(TypicalSubTask)),
) -> list[TypicalSubTaskFrontRead]:
    return await base_model_get(
        response,
        session,
        crud,
        pagination,
        query_filter,
        ordering,
        crud._select_model,
        TypicalSubTaskFrontRead,
    )


@router.post("/sub-task")
async def post_sub_task(
    data: TypicalSubTaskCreate,
    session: AsyncSession = Depends(get_session),
    crud: TypicalSubTaskCrud = Depends(get_typical_task_crud),
) -> TypicalSubTaskFrontRead:
    res = await crud.create(session, obj_in=data)
    await session.commit()
    return res


@router.post("/grimuar", status_code=204)
async def post_grimuar(
    data: CSVGrimuarExtractor = Depends(CSVGrimuarExtractor.from_body),
    session: AsyncSession = Depends(get_session),
    crud: TypicalSubTaskCrud = Depends(get_typical_task_crud),
):
    await crud.bulk_create(session, data.data)
    await session.commit()


# group
@router.get("/group")
async def get_group(
    response: Response,
    session: AsyncSession = Depends(get_session),
    ex_crud: ExtendedTaskGroupCrud = Depends(get_extended_group_crud),
    pagination: Paginator = Depends(paginator100),
    query_filter: TaskGroupFilter = FilterDepends(TaskGroupFilter),
    ordering: Ordering = OrderDepends(Ordering(TaskGroup)),
) -> list[TaskGroupFrontRead]:
    return await base_model_get(
        response,
        session,
        ex_crud,
        pagination,
        query_filter,
        ordering,
        ex_crud._select_model,
        TaskGroupFrontRead,
    )


@router.post("/group")
async def post_group(
    data: TaskGroupFrontCreate,
    session: AsyncSession = Depends(get_session),
    crud: TaskGroupCrud = Depends(get_group_crud),
    ex_crud: ExtendedTaskGroupCrud = Depends(get_extended_group_crud),
) -> TaskGroupFrontRead:
    res: TaskGroup = await crud.extended_create(session, data)
    await session.commit()
    fin = await ex_crud.get_one(session, id=res.id)
    return fin


@router.post("/groups", deprecated=True)
async def post_groups(
    data: list[TaskGroupFrontCreate],
    session: AsyncSession = Depends(get_session),
    crud: TaskGroupCrud = Depends(get_group_crud),
    ex_crud: ExtendedTaskGroupCrud = Depends(get_extended_group_crud),
) -> TaskGroupFrontRead:
    res: TaskGroup = await crud.extended_create(session, data)
    await session.commit()
    fin = await ex_crud.get_one(session, id=res.id)
    return fin
