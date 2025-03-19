from functools import cache
from typing import TYPE_CHECKING
from sqlalchemy import insert
from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession
from hmm.models.expedition import Chronicles, ExpeditionTemplate
from hmm.crud.base import CRUDBase
from hmm.models.tasks.group import TaskGroup
from hmm.schemas.expedition import (
    ChroniclesCreate,
    ChroniclesFrontRead,
    ExpeditionTemplateCreate,
    ExpeditionTemplateFrontCreate,
    ExpeditionTemplateFrontRead,
    Task2ExpeditionRead,
)

if TYPE_CHECKING:
    from hmm.models.expedition import Task2Expedition


@cache
def get_Task2Expedition() -> "Task2Expedition":
    from hmm.models.expedition import Task2Expedition

    return Task2Expedition


class ExpeditionTemplateCrud(
    CRUDBase[
        ExpeditionTemplate,
        ExpeditionTemplateFrontRead,
        ExpeditionTemplateCreate,
    ]
):

    async def create_with_tasks(
        self, session: AsyncSession, data: ExpeditionTemplateFrontCreate
    ) -> ExpeditionTemplate:
        res = await self.create(session, obj_in=data.to_db())
        t2g = []
        for ti in data.tasks:
            t2g.append(
                Task2ExpeditionRead(
                    group_id=ti, expedition_id=res.id
                ).model_dump()
            )
        ins_stmt = insert(get_Task2Expedition()).values(t2g)
        await session.execute(ins_stmt)
        return res


class ExtendedExpeditionTemplateCrud(ExpeditionTemplateCrud):

    @property
    def _select_model(self):
        return super()._select_model.options(
            selectinload(self.model.tasks).selectinload(TaskGroup.sub_task)
        )


class ChroniclesCrud(
    CRUDBase[Chronicles, ChroniclesFrontRead, ChroniclesCreate]
):
    pass


@cache
def get_chronicle_crud():
    return ChroniclesCrud()


@cache
def get_extended_expedition_template_crud():
    return ExtendedExpeditionTemplateCrud()


@cache
def get_expedition_template_crud():
    return ExpeditionTemplateCrud()
