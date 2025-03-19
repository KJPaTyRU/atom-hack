from functools import cache
from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from hmm.models.base import Base, UUIDDateCreatedMixin, BoundDbModel

if TYPE_CHECKING:
    from hmm.models.tasks.subtask_tasks import TypicalSubTask
    from hmm.models.tasks.task_group import Task2Group


@cache
def get_Task2Group() -> type["Task2Group"]:
    from hmm.models.tasks.task_group import Task2Group

    return Task2Group


class TaskGroup(BoundDbModel, UUIDDateCreatedMixin, Base):
    name: Mapped[str] = mapped_column(String(256), server_default="")

    sub_task: Mapped[list["TypicalSubTask"]] = ...

    @classmethod
    def bound_date_column(cls):
        return cls.created_at


TaskGroup.sub_task = relationship(
    "TypicalSubTask",
    secondary=get_Task2Group().__tablename__,
    # primaryjoin=get_Task2Group().group_id == TaskGroup.id,
    # secondaryjoin=get_Task2Group().group_id == TaskGroup.id,
    uselist=True,
)
