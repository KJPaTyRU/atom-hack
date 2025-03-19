from functools import cache
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import insert, select
from sqlalchemy.orm import selectinload, joinedload

from sqlalchemy.ext.asyncio import AsyncSession
from hmm.enum import ExpeditionStatus
from hmm.models.expedition import ExpeditionTemplate
from hmm.crud.base import CRUDBase
from hmm.models.tasks.group import TaskGroup
from hmm.schemas.expedition import (
    ExpeditionTemplateCreate,
    ExpeditionTemplateFrontRead,
    Heroes2ExpeditionRead,
    Task2ExpeditionRead,
)

if TYPE_CHECKING:
    from hmm.models.expedition import Task2Expedition
    from hmm.models.expedition import Heroes2Expedition


@cache
def get_Task2Expedition() -> "Task2Expedition":
    from hmm.models.expedition import Task2Expedition

    return Task2Expedition


@cache
def get_Heroes2Expedition() -> "Heroes2Expedition":
    from hmm.models.expedition import Heroes2Expedition

    return Heroes2Expedition


def flatten_tasks(obj: ExpeditionTemplate):
    ret = []
    for tgi in obj.tasks:
        ret.extend(tgi.sub_task)
    return ret


class ExpeditionTemplateCrud(
    CRUDBase[
        ExpeditionTemplate,
        ExpeditionTemplateFrontRead,
        ExpeditionTemplateCreate,
    ]
):

    async def insert_tasks(
        self, session: AsyncSession, tasks: list[uuid.UUID], to_: uuid.UUID
    ):
        t2g = []
        for ti in tasks:
            t2g.append(
                Task2ExpeditionRead(
                    group_id=ti, expedition_id=to_
                ).model_dump()
            )

        ins_stmt = insert(get_Task2Expedition()).values(t2g)
        await session.execute(ins_stmt)

    async def insert_heroes(
        self, session: AsyncSession, heroes: list[uuid.UUID], to_: uuid.UUID
    ):
        t2g = []
        for ti in heroes:
            t2g.append(
                Heroes2ExpeditionRead(
                    hero_id=ti, expedition_id=to_
                ).model_dump()
            )

        ins_stmt = insert(get_Heroes2Expedition()).values(t2g)
        await session.execute(ins_stmt)

    async def extended_create(
        self, session: AsyncSession, data: ExpeditionTemplateCreate
    ) -> ExpeditionTemplate:
        rd = data.to_db()
        res = await self.create(session, obj_in=rd)
        await self.insert_tasks(session, data.tasks, res.id)
        # await self.insert_heroes(session, data.tasks, res.id)
        return res

    async def set_status(
        self, session: AsyncSession, to_: uuid.UUID, status: ExpeditionStatus
    ):
        await self.update(
            session,
            update_filter=dict(id=to_),
            update_values=dict(status=status),
        )

    async def get_subtasks(self, session: AsyncSession, to_: uuid.UUID):
        stmt = (
            select(ExpeditionTemplate)
            .options(
                selectinload(ExpeditionTemplate.tasks).selectinload(
                    TaskGroup.sub_task
                )
            )
            .where(ExpeditionTemplate.id == to_)
        )
        res = (await session.execute(stmt)).scalar_one()
        return flatten_tasks(res)


class ExtendedExpeditionTemplateCrud(ExpeditionTemplateCrud):

    @property
    def _select_model(self):
        return super()._select_model.options(
            selectinload(self.model.tasks).selectinload(TaskGroup.sub_task),
            selectinload(self.model.heroes),
            joinedload(self.model.author),
        )


@cache
def get_extended_expedition_template_crud():
    return ExtendedExpeditionTemplateCrud()


@cache
def get_expedition_template_crud():
    return ExpeditionTemplateCrud()
