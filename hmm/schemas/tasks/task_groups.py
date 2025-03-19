import uuid
from hmm.schemas.base import OrmModel


class Task2GroupCreate(OrmModel):
    group_id: uuid.UUID
    typical_task: uuid.UUID


class Task2GroupRead(OrmModel):
    group_id: uuid.UUID
    typical_task: uuid.UUID
