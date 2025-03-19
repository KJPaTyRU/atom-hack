import datetime
import uuid
from hmm.schemas.base import CreatedTimeSchemaMixin, OrmModel, IntIdSchemaMixin


class HeroUsedTimeTableFields(OrmModel):
    hero_id: uuid.UUID
    expedition_id: uuid.UUID
    date_start: datetime.datetime
    date_end: datetime.datetime


class HeroUsedTimeTableCreate(HeroUsedTimeTableFields):
    pass


class HeroUsedTimeTableFrontRead(
    HeroUsedTimeTableFields, IntIdSchemaMixin, CreatedTimeSchemaMixin
):
    pass
