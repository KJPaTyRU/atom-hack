import datetime
import uuid
from pydantic import Field
from hmm.schemas.base import (
    CreatedTimeSchemaMixin,
    OrmModel,
    UuidIdSchemaMixin,
)
from hmm.schemas.hero import HeroFrontRead
from hmm.schemas.tasks.group import TaskGroupFrontRead


# * ExpeditionTemplate * #
class BaseExpeditionTemplateFields(OrmModel):
    name: str = Field(max_length=256)
    description: str = ""


class ExpeditionTemplateCreate(BaseExpeditionTemplateFields):
    pass


class ExpeditionTemplateFrontCreate(BaseExpeditionTemplateFields):
    tasks: list[uuid.UUID] = Field(
        description="Список задач в шаблоне экспедиции",
        default_factory=list,
        min_length=1,
    )

    def to_db(self, **kwargs) -> ExpeditionTemplateCreate:
        return ExpeditionTemplateCreate.model_validate(self)


class ExpeditionTemplateFrontRead(
    BaseExpeditionTemplateFields, UuidIdSchemaMixin, CreatedTimeSchemaMixin
):
    tasks: list[TaskGroupFrontRead] = Field(
        description="Список задач в шаблоне экспедиции", default_factory=list
    )


class Task2ExpeditionRead(OrmModel):
    group_id: uuid.UUID
    expedition_id: uuid.UUID


# * Chronicles * #
class BaseChroniclesFields(OrmModel):
    name: str = Field(max_length=256)
    description: str = ""
    date_start: datetime.datetime
    date_end: datetime.datetime


class ChroniclesCreate(BaseChroniclesFields):
    expedition_template_id: uuid.UUID
    author_id: int


class ChroniclesFrontCreate(BaseChroniclesFields):
    expedition_template_id: uuid.UUID


class ChroniclesFrontRead(
    BaseChroniclesFields, UuidIdSchemaMixin, CreatedTimeSchemaMixin
):
    expedition: ExpeditionTemplateFrontRead
    heroies: list[HeroFrontRead] = Field(default_factory=list, min_length=1)
