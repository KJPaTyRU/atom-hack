import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from hmm.models.base import Base, DateCreatedMixin, BoundDbModel
from hmm.models.tasks.group import TaskGroup
from hmm.models.tasks.subtask_tasks import TypicalSubTask


class Task2Group(BoundDbModel, DateCreatedMixin, Base):
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(TaskGroup.id, ondelete="CASCADE"), primary_key=True
    )
    typical_task: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(TypicalSubTask.id, ondelete="CASCADE"), primary_key=True
    )

    @classmethod
    def bound_date_column(cls):
        return cls.created_at
