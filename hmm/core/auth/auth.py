import base64
from datetime import datetime
from functools import cache
from fastapi import Depends, Request, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_serializer,
    model_validator,
)
from jose import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from hmm.config import get_settings
from hmm.core.db import AsyncSessionMaker
from hmm.crud.auth import get_user_crud
from hmm.models.auth import User
from hmm.schemas.auth import (
    SecPasswordStr,
    UpdateUser,
    UserCreate,
    UserNameStr,
    UserPatchMe,
    UserSession,
)
from hmm.schemas.base import OrmModel
from hmm.core.crypto import get_fernet, verify_password
from hmm.core.exceptions import (
    BadCredsError,
    BaseArgsRestException,
    NotASuperUserException,
    PasswordError,
    RegistrationError,
    TokenSchemaError,
)

# * Schemas * #


class UserLogin(OrmModel):
    username: UserNameStr
    password: SecPasswordStr


class UserRegister(OrmModel):
    username: UserNameStr
    password1: SecPasswordStr
    password2: SecPasswordStr
    is_super: bool = False

    @model_validator(mode="after")
    def validate_model(self):
        if self.password1 != self.password2:
            raise ValueError("password1 != password2")
        return self

    @computed_field
    @property
    def password(self) -> SecPasswordStr:
        return self.password1


# * Manager * #


class CookieData(BaseModel):
    username: str
    date: int = Field(default_factory=lambda: int(datetime.now().timestamp()))


class BaseAuthSchema:

    def get_cookie(self, ses: UserSession) -> str:
        pass

    def login(self, r: Response, ses: UserSession):
        pass

    def logout(self, r: Response):
        pass

    def authenticate(self, r: Request) -> CookieData:
        pass


class CookieSchema(BaseAuthSchema):

    KEY = "creds"

    def get_cookie(self, ses: UserSession) -> str:
        c = CookieData(username=ses.username)
        d0 = c.model_dump_json().encode()
        d1 = get_fernet().encrypt(d0)
        d2 = base64.urlsafe_b64encode(d1).decode()
        return d2

    def login(self, r: Response, ses: UserSession):
        hashed = self.get_cookie(ses)
        r.set_cookie(
            self.KEY,
            hashed,
            max_age=get_settings().auth.max_age,
            secure=True,
            httponly=True,
            samesite="strict",
        )

    def logout(self, r: Response):
        r.delete_cookie(
            self.KEY, secure=True, httponly=True, samesite="strict"
        )

    def _authenticate(self, r: Request) -> CookieData:
        d0 = r.cookies[self.KEY]
        d1 = base64.urlsafe_b64decode(d0)
        d2 = get_fernet().decrypt(d1)
        return CookieData.model_validate_json(d2)

    def authenticate(self, r: Request) -> CookieData:
        try:
            return self._authenticate(r)
        except Exception as e:
            raise BadCredsError(details=dict(error=str(e)))


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=get_settings().api.cdn_prefix + "/auth/login/form",
    # tokenUrl=get_settings().api.cur_prefix + "/auth/login/form",
    auto_error=False,
)


class AccessToken(OrmModel):
    access_token: str


class LoginResponse(AccessToken):
    token_type: str = "bearer"


AUDIENCE = [get_settings().app.name]


@cache
def utc_offset():
    return datetime.now() - datetime.utcnow()


class TokenPayload(OrmModel):
    iat: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    aud: list[str] = Field(default_factory=lambda: AUDIENCE)
    sub: int = Field(description="user_id")
    una: str = Field(description="username")

    @computed_field
    @property
    def exp(self) -> int:
        return self.iat + self.lifetime

    @field_serializer("sub", when_used="json")
    @classmethod
    def sub_to_str(cls, v):
        if isinstance(v, str):
            return v
        return str(v)

    @property
    def lifetime(self):
        return get_settings().auth.max_age

    @classmethod
    def jwt_decode(cls, data: str):
        try:
            d = jwt.decode(
                data,
                get_settings().auth.jwt_secret,
                algorithms=[get_settings().auth.jwt_algorithm],
                audience=get_settings().app.name,
                options={"leeway": utc_offset()},
            )
            return cls(**d)
        except Exception as e:
            raise BadCredsError(details=dict(error=str(e)))

    def jwt_encode(self) -> str:
        return jwt.encode(
            self.model_dump(mode="json"),
            get_settings().auth.jwt_secret,
            algorithm=get_settings().auth.jwt_algorithm,
        )


class TokenSchema(BaseAuthSchema):

    def login(self, r: Response, ses: UserSession) -> LoginResponse:
        token = TokenPayload(sub=ses.id, una=ses.username).jwt_encode()
        return LoginResponse(access_token=token)

    def logout(self, r: Response):
        pass

    def authenticate(self, r: Request) -> CookieData:
        authorization = r.headers["Authorization"]
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            raise TokenSchemaError()
        token = TokenPayload.jwt_decode(param)
        return CookieData(username=token.una, date=token.iat)


class UserSessionManager:

    def __init__(self, schema: BaseAuthSchema | None = None) -> None:
        self.schema = schema
        if self.schema is None:
            self.schema = CookieSchema()

    async def login(
        self, session: AsyncSession, creds: UserLogin
    ) -> UserSession:
        user = await get_user_crud().get_one(
            session, [User.username == creds.username]
        )
        if not verify_password(creds.password, user.hashed_password):
            raise PasswordError(details=dict(info="password1 != password2"))
        return UserSession.model_validate(user)

    async def register(
        self, session: AsyncSession, creds: UserRegister
    ) -> UserSession:
        try:
            data = UserCreate.model_validate(creds)
            user = await get_user_crud().create(session, obj_in=data)
            return UserSession.model_validate(user)
        except BaseArgsRestException:
            raise
        except IntegrityError as e:
            if e.orig.pgcode == "23505":
                raise RegistrationError(details=dict(error="Illegal username"))
            raise
        except Exception as e:
            raise RegistrationError(details=dict(error=str(e)))

    async def logout(self, session: AsyncSession, user: UserSession):
        pass

    async def authenticate(
        self, request: Request, response: Response
    ) -> UserSession:
        c = self.schema.authenticate(request)
        async with AsyncSessionMaker() as session:
            user = await get_user_crud().get_one(
                session, [User.username == c.username]
            )
            t = user.updated_at.timestamp()
            if not user.is_active or t > c.date:
                await self.logout(session, user)
                self.schema.logout(response)
                raise BadCredsError(details=dict(error="Incorrect creds"))
        return user

    async def patch(
        self,
        session: AsyncSession,
        user: UserSession,
        data: UserPatchMe,
        force: bool = True,
    ) -> User:
        where = [User.id == user.id]
        crud = get_user_crud()
        ndata = data.model_patch(user)
        if ndata:
            await crud.update(session, where, ndata)
        res = await crud.get_one_raw(session, where)
        if force:
            await session.commit()
        return res

    async def update(
        self, session: AsyncSession, data: UpdateUser, force: bool = True
    ) -> User:
        where = [User.username == data.username]
        crud = get_user_crud()
        cuser = await crud.get_one_raw(session, where)

        ndata = data.model_patch(cuser)
        if ndata:
            await crud.update(session, where, ndata)

        await session.refresh(cuser)
        if force:
            await session.commit()
        return cuser


@cache
def get_usm() -> UserSessionManager:
    return UserSessionManager()


@cache
def get_usm_token() -> UserSessionManager:
    return UserSessionManager(TokenSchema())


class TmpRequest:
    def __init__(self, token: str):
        self.headers = {"Authorization": f"Bearer {token}"}


class TmpResponse:
    def __init__(self, token: str):
        self.headers = {"Authorization": f"Bearer {token}"}


async def authenticate_user_socket(
    token: str | None = Depends(oauth2_scheme),
    manager: UserSessionManager = Depends(get_usm_token),
) -> UserSession:
    if token is None:
        raise BadCredsError()
    request = TmpRequest(token)
    response = TmpResponse(token)
    return await manager.authenticate(request, response)


async def authenticate_user(
    request: Request,
    response: Response,
    token: str | None = Depends(oauth2_scheme),
    # manager: UserSessionManager = Depends(get_usm),
    manager: UserSessionManager = Depends(get_usm_token),
) -> UserSession:
    user = await manager.authenticate(request, response)
    return user


async def authenticate_superuser(
    request: Request,
    response: Response,
    token: str | None = Depends(oauth2_scheme),
    # manager: UserSessionManager = Depends(get_usm),
    manager: UserSessionManager = Depends(get_usm_token),
) -> UserSession:
    user = await authenticate_user(request, response, token, manager)
    if not user.is_super:
        raise NotASuperUserException
    return user
