import datetime
from typing import Annotated

from pydantic import Field, StringConstraints, computed_field
from hmm.schemas.base import CreatedTimeSchemaMixin, OrmModel
from hmm.core.crypto import get_hashed_password, verify_password

UserNameStr = Annotated[
    str,
    StringConstraints(
        min_length=4,
        max_length=64,
        to_lower=True,
        pattern=r"(\w|\d|[_\-.]){4,64}",
    ),
]
SecPasswordStr = Annotated[
    str,
    StringConstraints(
        min_length=4,
        max_length=128,
        pattern=r"(\w|\d|[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]){4,128}",
    ),
]


class UserRawCreate(OrmModel):
    username: UserNameStr
    is_super: bool = False
    is_active: bool = True


class UserCreate(UserRawCreate):
    password: SecPasswordStr = Field(exclude=True)

    @computed_field
    @property
    def hashed_password(self) -> str:
        return get_hashed_password(self.password)


class UserPatch(OrmModel):
    password: SecPasswordStr | None = Field(None)

    def model_patch(self, user: "UserSession") -> dict:
        data = self.model_dump(exclude_unset=True, exclude_none=True)
        if "password" in data and data["password"] is not None:
            new_password = data.pop("password")
            if not verify_password(new_password, user.hashed_password):
                data["hashed_password"] = get_hashed_password(new_password)
                data["updated_at"] = datetime.datetime.now()
        return data


class UserPatchMe(UserPatch):
    username: UserNameStr


class UpdateUser(UserPatch):
    username: UserNameStr
    is_super: bool | None = Field(None)
    is_active: bool | None = Field(None)


class UserRead(CreatedTimeSchemaMixin):
    username: UserNameStr


class User(UserRawCreate):
    id: int
    hashed_password: str = Field(exclude=True)


class UserFront(User, CreatedTimeSchemaMixin):
    pass


class UserSession(UserFront):
    updated_at: datetime.datetime
