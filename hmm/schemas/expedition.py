import datetime
import uuid
from pydantic import Field
from hmm.core.types import ManaFloatType
from hmm.enum import ExpeditionStatus
from hmm.schemas.auth import UserRead
from hmm.schemas.base import (
    CreatedTimeSchemaMixin,
    OrmModel,
    UuidIdSchemaMixin,
)
from hmm.schemas.hero import HeroFrontRead
from hmm.schemas.tasks.group import TaskGroupFrontCreate, TaskGroupFrontRead


# * ExpeditionTemplate * #
class ExpeditionDetails(OrmModel):
    w_mana: ManaFloatType = 0
    m_mana: ManaFloatType = 0
    s_mana: ManaFloatType = 0
    total_mana: ManaFloatType = 0


class BaseExpeditionTemplateFields(OrmModel):
    name: str = Field(max_length=256)
    description: str = ""
    date_start: datetime.datetime
    date_end: datetime.datetime


class ExpeditionTemplateCreate(
    BaseExpeditionTemplateFields, ExpeditionDetails
):
    tasks: list[uuid.UUID] = Field(
        description="Список задач в шаблоне экспедиции",
        default_factory=list,
        min_length=1,
    )
    heroes: list[uuid.UUID] = Field(default_factory=list)
    author_id: int
    status: ExpeditionStatus = ExpeditionStatus.created

    def to_db(self, **kwargs):
        return self.model_dump(
            exclude_unset=True, exclude_none=True, exclude={"tasks", "heroes"}
        )


class ExpeditionTemplateFrontCreate(BaseExpeditionTemplateFields):
    tasks: list[uuid.UUID] = Field(
        description="Список задач в шаблоне экспедиции",
        default_factory=list,
        min_length=1,
    )
    # heroes: list[uuid.UUID] = Field(default_factory=list)

    def to_db(self, author_id: int, **kwargs) -> ExpeditionTemplateCreate:
        data = self.model_dump()
        data["author_id"] = author_id
        return ExpeditionTemplateCreate(**data)


class ExpeditionTemplateFrontFullCreate(BaseExpeditionTemplateFields):
    tasks: list[TaskGroupFrontCreate] = Field(
        description="Список задач в шаблоне экспедиции",
        default_factory=list,
        min_length=1,
    )

    def to_db(
        self, author_id: int, tasks_ids: list[uuid.UUID], **kwargs
    ) -> ExpeditionTemplateCreate:
        data = self.model_dump()
        data["author_id"] = author_id
        data["tasks"] = tasks_ids
        return ExpeditionTemplateCreate(**data)


class ExpeditionTemplateFrontRead(
    BaseExpeditionTemplateFields,
    UuidIdSchemaMixin,
    CreatedTimeSchemaMixin,
    ExpeditionDetails,
):
    status: ExpeditionStatus = ExpeditionStatus.created
    tasks: list[TaskGroupFrontRead] = Field(
        description="Список задач в шаблоне экспедиции", default_factory=list
    )
    heroes: list[HeroFrontRead] = Field(default_factory=list)
    author: UserRead


class Task2ExpeditionRead(OrmModel):
    group_id: uuid.UUID
    expedition_id: uuid.UUID


class Heroes2ExpeditionRead(OrmModel):
    hero_id: uuid.UUID
    expedition_id: uuid.UUID
