import uuid
from pydantic import Field
from hmm.schemas.base import (
    CreatedTimeSchemaMixin,
    OrmModel,
    UuidIdSchemaMixin,
)
from hmm.schemas.tasks.subtask_tasks import (
    TypicalSubTaskCreate,
    TypicalSubTaskFrontRead,
)

# from hmm.schemas.tasks.subtask_tasks import TypicalSubTaskCreate


# * TaskGroup * #
class BaseTaskGroupFields(OrmModel):
    name: str = Field(max_length=256)
    # description: str = ""


class TaskGroupCreate(BaseTaskGroupFields):
    pass


class TaskGroupFrontCreate(BaseTaskGroupFields):
    sub_task: list[uuid.UUID] = Field(default_factory=list, min_length=1)

    def to_db(self, **kwargs) -> TaskGroupCreate:
        return TaskGroupCreate.model_validate(self)


class TaskGroupFrontFullCreate(BaseTaskGroupFields):
    sub_task: list[TypicalSubTaskCreate] = Field(
        default_factory=list, min_length=1
    )

    def to_db(self, **kwargs) -> TaskGroupCreate:
        return TaskGroupCreate.model_validate(self)


class TaskGroupFrontRead(
    BaseTaskGroupFields, UuidIdSchemaMixin, CreatedTimeSchemaMixin
):
    sub_task: list[TypicalSubTaskFrontRead] = Field(default_factory=list)
