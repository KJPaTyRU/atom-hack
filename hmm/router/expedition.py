from fastapi import APIRouter, BackgroundTasks, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from hmm.core.auth.auth import authenticate_user
from hmm.core.db import get_session
from hmm.core.exceptions import GroupCreationErrorError
from hmm.core.filtering.base import FilterDepends
from hmm.core.ordering import OrderDepends, Ordering
from hmm.core.paginator import Paginator, paginator100
from hmm.crud.expedition import (
    ExpeditionTemplateCrud,
    ExtendedExpeditionTemplateCrud,
    get_expedition_template_crud,
    get_extended_expedition_template_crud,
)
from hmm.crud.tasks.group import get_group_crud
from hmm.filters.expedition import ExpeditionTemplateFilter
from hmm.models.expedition import ExpeditionTemplate
from hmm.router.base import base_model_get
from hmm.schemas.auth import UserSession
from hmm.schemas.expedition import (
    ExpeditionTemplateFrontCreate,
    ExpeditionTemplateFrontFullCreate,
    ExpeditionTemplateFrontRead,
)
from hmm.usecase.heroes_autopick import get_hap_usecase

router = APIRouter(
    prefix="",
    dependencies=[Depends(authenticate_user)],
    tags=["Expedition & Chronics"],
)


def get_router() -> APIRouter:
    return router


# expedition
@router.get("/expedition")
async def get_expedition_templates(
    response: Response,
    session: AsyncSession = Depends(get_session),
    crud: ExtendedExpeditionTemplateCrud = Depends(
        get_extended_expedition_template_crud
    ),
    pagination: Paginator = Depends(paginator100),
    query_filter: ExpeditionTemplateFilter = FilterDepends(
        ExpeditionTemplateFilter
    ),
    ordering: Ordering = OrderDepends(Ordering(ExpeditionTemplate)),
) -> list[ExpeditionTemplateFrontRead]:
    res = await base_model_get(
        response,
        session,
        crud,
        pagination,
        query_filter,
        ordering,
        crud._select_model,
        ExpeditionTemplateFrontRead,
    )
    return res


@router.post("/expedition")
async def post_expedition(
    background_tasks: BackgroundTasks,
    data: ExpeditionTemplateFrontCreate,
    crud: ExpeditionTemplateCrud = Depends(get_expedition_template_crud),
    session: AsyncSession = Depends(get_session),
    ex_crud: ExtendedExpeditionTemplateCrud = Depends(
        get_extended_expedition_template_crud
    ),
    user: UserSession = Depends(authenticate_user),
) -> ExpeditionTemplateFrontRead:
    res = await crud.extended_create(session, data.to_db(user.id))
    await session.commit()
    background_tasks.add_task(get_hap_usecase().process, res.id)
    fin = await ex_crud.get_one(session, id=res.id)
    return fin


@router.post("/expedition-full")
async def post_expedition_full(
    background_tasks: BackgroundTasks,
    data: ExpeditionTemplateFrontFullCreate,
    crud: ExpeditionTemplateCrud = Depends(get_expedition_template_crud),
    session: AsyncSession = Depends(get_session),
    ex_crud: ExtendedExpeditionTemplateCrud = Depends(
        get_extended_expedition_template_crud
    ),
    user: UserSession = Depends(authenticate_user),
) -> ExpeditionTemplateFrontRead:

    # Group
    groups = await get_group_crud().extended_create_many(session, data.tasks)

    if not groups:
        raise GroupCreationErrorError()
    await session.flush()
    task_ids = [gi.id for gi in groups]
    # expedition
    res = await crud.extended_create(session, data.to_db(user.id, task_ids))
    await session.commit()
    background_tasks.add_task(get_hap_usecase().process, res.id)
    fin = await ex_crud.get_one(session, id=res.id)
    return fin
