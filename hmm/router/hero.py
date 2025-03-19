from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from hmm.core.auth.auth import authenticate_user
from hmm.core.db import get_session
from hmm.core.filtering.base import FilterDepends
from hmm.core.ordering import OrderDepends, Ordering
from hmm.core.paginator import Paginator, paginator100
from hmm.crud.hero import HeroCrud, get_hero_crud
from hmm.filters.hero import HeroFilter
from hmm.models.hero import Hero
from hmm.router.base import base_model_get
from hmm.schemas.hero import HeroCreate, HeroFrontRead

router = APIRouter(
    prefix="/hero", dependencies=[Depends(authenticate_user)], tags=["Hero"]
)


def get_router() -> APIRouter:
    return router


# sub-task
@router.get("")
async def get_hero(
    response: Response,
    session: AsyncSession = Depends(get_session),
    crud: HeroCrud = Depends(get_hero_crud),
    pagination: Paginator = Depends(paginator100),
    query_filter: HeroFilter = FilterDepends(HeroFilter),
    ordering: Ordering = OrderDepends(Ordering(Hero)),
) -> list[HeroFrontRead]:
    return await base_model_get(
        response,
        session,
        crud,
        pagination,
        query_filter,
        ordering,
        crud._select_model,
        HeroFrontRead,
    )


@router.post("")
async def post_hero(
    data: HeroCreate,
    session: AsyncSession = Depends(get_session),
    crud: HeroCrud = Depends(get_hero_crud),
) -> HeroFrontRead:
    res = await crud.create(session, obj_in=data)
    await session.commit()
    return res
