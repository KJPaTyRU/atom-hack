from functools import cache

from hmm.models.auth import User
from hmm.crud.base import CRUDBase
from hmm.schemas.auth import UserCreate, UserSession


class UserCrud(CRUDBase[User, UserSession, UserCreate]):
    pass


@cache
def get_user_crud():
    return UserCrud()
