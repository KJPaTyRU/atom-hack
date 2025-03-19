from pydantic import Field
from hmm.core.types import ManaFloatType, TaskLvl
from hmm.enum import SubTaskType
from hmm.schemas.base import (
    CreatedTimeSchemaMixin,
    OrmModel,
    UuidIdSchemaMixin,
)


# * TaskGroup * #
class TypicalSubTask(OrmModel):
    name: str = Field(max_length=256)
    # description: str = ""

    task_type: SubTaskType
    task_lvl: TaskLvl
    w_mana: ManaFloatType
    m_mana: ManaFloatType
    s_mana: ManaFloatType


class TypicalSubTaskCreate(TypicalSubTask):
    pass


class TypicalSubTaskFrontRead(
    TypicalSubTask, UuidIdSchemaMixin, CreatedTimeSchemaMixin
):
    pass
