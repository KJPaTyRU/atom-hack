from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from hmm.core.auth.auth import (
    LoginResponse,
    UserLogin,
    UserRegister,
    UserSession,
    UserSessionManager,
    authenticate_superuser,
    authenticate_user,
    get_usm,
    get_usm_token,
)
from hmm.crud.auth import UserCrud, get_user_crud
from hmm.core.db import get_session
from hmm.filters.user import UserFilter
from hmm.models.auth import User
from hmm.router.base import base_model_get
from hmm.schemas.auth import (
    UpdateUser,
    UserFronCreate,
    UserFront,
    UserPatchMe,
    UserRead,
    UserRoledRead,
)
from hmm.core.filtering.base import FilterDepends
from hmm.core.ordering import Ordering
from hmm.core.paginator import Paginator, default_paginator

auth_router = APIRouter()
sec_router = APIRouter(dependencies=[Depends(authenticate_user)])
sup_sec_router = APIRouter(dependencies=[Depends(authenticate_superuser)])


def get_router() -> APIRouter:
    router = APIRouter()
    router.include_router(auth_router, prefix="/auth", tags=["Auth"])
    router.include_router(sec_router, prefix="/user", tags=["User"])
    router.include_router(sup_sec_router, prefix="/user", tags=["User"])
    return router


@auth_router.post("/login/form", include_in_schema=True)
async def user_login_form(
    response: Response,
    creds: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
    manager: UserSessionManager = Depends(get_usm_token),
) -> LoginResponse:
    ses = await manager.login(session, UserLogin.model_validate(creds))
    return manager.schema.login(response, ses)


@auth_router.post("/login")
async def user_login(
    response: Response,
    creds: UserLogin,
    session: AsyncSession = Depends(get_session),
    manager: UserSessionManager = Depends(get_usm_token),
) -> LoginResponse:
    ses = await manager.login(session, creds)
    return manager.schema.login(response, ses)


@auth_router.get("/logout", status_code=204)
async def get_logout(
    response: Response,
    user: UserSession = Depends(authenticate_user),
    session: AsyncSession = Depends(get_session),
    manager: UserSessionManager = Depends(get_usm),
):
    await manager.logout(session, user)
    manager.schema.logout(response)


@auth_router.post("/registration")
async def post_registration(
    data: UserFronCreate,
    session: AsyncSession = Depends(get_session),
    crud: UserCrud = Depends(get_user_crud),
) -> UserFront:
    user = await crud.create(session, obj_in=data.to_db_schema())
    await session.commit()
    return user


@sup_sec_router.get("")
async def get_users(
    response: Response,
    session: AsyncSession = Depends(get_session),
    crud: UserCrud = Depends(get_user_crud),
    pagination: Paginator = Depends(default_paginator),
    query_filter: UserFilter = FilterDepends(UserFilter),
    ordering: Ordering = Depends(Ordering(User)),
) -> list[UserFront]:
    return await base_model_get(
        response,
        session,
        crud,
        pagination,
        query_filter,
        ordering,
        crud._select_model,
        UserFront,
        execute_scalars=True,
        add_bound_date_header=True,
    )


@sup_sec_router.post("")
async def user_create(
    creds: UserRegister,
    session: AsyncSession = Depends(get_session),
    manager: UserSessionManager = Depends(get_usm),
) -> UserSession:
    ses = await manager.register(session, creds)
    await session.commit()
    return ses


@sup_sec_router.patch("")
async def user_patch(
    creds: UpdateUser,
    session: AsyncSession = Depends(get_session),
    manager: UserSessionManager = Depends(get_usm),
) -> UserSession:
    return await manager.update(session, creds)


@sec_router.get("/me")
async def get_me(
    user: UserSession = Depends(authenticate_user),
) -> UserRoledRead:
    return UserRoledRead.model_validate(user)


@sec_router.patch("/me")
async def patch_me(
    data: UserPatchMe,
    session: AsyncSession = Depends(get_session),
    manager: UserSessionManager = Depends(get_usm),
    user: UserSession = Depends(authenticate_user),
) -> UserRead:
    return await manager.patch(session, user, data)
