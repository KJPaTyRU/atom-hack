from functools import cache

from hmm.models.tasks.task_group import Task2Group
from hmm.crud.base import CRUDBase
from hmm.schemas.tasks.task_groups import Task2GroupCreate, Task2GroupRead


class Task2GroupCrud(CRUDBase[Task2Group, Task2GroupRead, Task2GroupCreate]):
    pass


@cache
def get_task_group_crud():
    return Task2GroupCrud()
