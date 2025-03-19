import datetime
import re
from copy import deepcopy
from typing import Annotated, Any, Optional, Tuple, Type
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    create_model,
)
from pydantic._internal._model_construction import ModelMetaclass
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

PhoneNumberStr = Annotated[str, StringConstraints(pattern=r"^\d{1,16}$")]
StripStr = Annotated[str, StringConstraints(True)]
KeySecretStr = Annotated[str, StringConstraints(True, pattern=r"[^:]+")]


NameStrPattern = r"^[a-zA-Z0-9_\-]+$"
ScopePattern = re.compile(NameStrPattern)


def hide_phone(phone: str):
    if len(phone) > 7:
        return phone[:2] + "***" + phone[-2:]
    return "***" + phone[-1]


def str_2_date(v: str):
    vd = datetime.datetime.strptime(v, "%d.%m.%Y")
    vd = vd.replace(tzinfo=datetime.timezone.utc)
    return datetime.date(day=vd.day, month=vd.month, year=vd.year)


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    def to_db(self, **kwargs):
        """Extra method for serialization data for the frontend"""
        return self.model_dump(exclude_unset=True, exclude_none=True)

    def to_front(self):
        """Extra method for serialization data for the frontend"""
        return self.model_dump(mode="json", by_alias=True)


class SyncTimeMixin(OrmModel):
    sync_time: datetime.datetime | None = None
    is_actual: bool = False


class DateTimeOrmModel(OrmModel):
    created_at: datetime.datetime | None = None
    last_modified: datetime.datetime | None = None


class CreatedTimeSchemaMixin(OrmModel):
    created_at: datetime.datetime = Field(
        description="Дата создания записи на сервере"
    )


class IntIdSchemaMixin(OrmModel):
    id: int = Field(description="Primary Key")


class UuidIdSchemaMixin(OrmModel):
    id: UUID = Field(description="Primary Key")


class AllOptional(ModelMetaclass):
    """Add as metaclass for   (metaclass=AllOptional)"""

    def __new__(mcs, name, bases, namespaces, **kwargs):
        annotations = namespaces.get("__annotations__", {})
        for base in bases:
            annotations.update(base.__annotations__)
        for field in annotations:
            if not field.startswith("__"):
                annotations[field] = annotations[field] | None
                # !!! Затирает дефолтные значения
                namespaces[field] = None
        namespaces["__annotations__"] = annotations
        return super().__new__(mcs, name, bases, namespaces, **kwargs)


def partial_model(model: Type[BaseModel]):
    def make_field_optional(
        field: FieldInfo, default: Any = None
    ) -> Tuple[Any, FieldInfo]:
        new = deepcopy(field)
        if field.default is PydanticUndefined:
            new.default = default
        new.annotation = Optional[field.annotation]  # type: ignore
        return new.annotation, new

    return create_model(
        f"Partial{model.__name__}",
        __base__=model,
        __module__=model.__module__,
        **{
            field_name: make_field_optional(field_info)
            for field_name, field_info in model.model_fields.items()
        },
    )


DYN_SPLIT_PATTERN = re.compile(r"[~:]")


class ClientType(OrmModel):
    full_id: str
    client_id: str
    tags: set
    is_dyn: bool = False

    @computed_field
    @property
    def is_force(self) -> bool:
        return "forced" in self.tags

    @classmethod
    def from_client_id(cls, client_id: str):
        t = DYN_SPLIT_PATTERN.split(client_id)
        is_dyn = False
        short_id = client_id
        tags = set()
        if len(t) <= 1:
            pass
        elif len(t) == 2:
            short_id = t[1]
            tags.add(t[0].lower())
        elif len(t) == 3:
            short_id = t[1]
            tags.add(t[0].lower())
            is_dyn = True
        else:
            raise ValueError("WTF?")
        if not is_dyn and "dyn" in tags:
            is_dyn = True
        return cls(
            full_id=client_id, client_id=short_id, tags=tags, is_dyn=is_dyn
        )
