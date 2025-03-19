from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from hmm.core.auth.auth import authenticate_user
from hmm.core.db import get_session
from hmm.core.filtering.base import FilterDepends
from hmm.core.ordering import OrderDepends, Ordering
from hmm.core.paginator import Paginator, paginator100
from hmm.crud.expedition import (
    ExpeditionTemplateCrud,
    ExtendedExpeditionTemplateCrud,
    get_expedition_template_crud,
    get_extended_expedition_template_crud,
)
from hmm.filters.expedition import ExpeditionTemplateFilter
from hmm.models.expedition import ExpeditionTemplate
from hmm.router.base import base_model_get
from hmm.schemas.auth import UserSession
from hmm.schemas.expedition import (
    ExpeditionTemplateFrontCreate,
    ExpeditionTemplateFrontRead,
)

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
    fin = await ex_crud.get_one(session, id=res.id)
    return fin
