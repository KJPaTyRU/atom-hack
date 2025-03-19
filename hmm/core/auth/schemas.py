import datetime
from hmm.schemas.base import CreatedTimeSchemaMixin, OrmModel


class AccessToken(OrmModel):
    access_token: str


class LoginResponse(AccessToken):
    token_type: str = "bearer"


class TokenExchangeLoginResponse(LoginResponse):
    refresh_token: str


class SudirLoginResponse(LoginResponse):
    expires_in: int
    refresh_token: str
    scope: str


class SudirAuthToken(OrmModel):
    code: str


class InnerTokenCreate(OrmModel):
    sub: str
    auth_token: str | None = None
    refresh_token: str | None = None


class InnerToken(InnerTokenCreate, CreatedTimeSchemaMixin):
    id: int
    created_at: datetime.datetime
