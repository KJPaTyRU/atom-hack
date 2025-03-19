# from functools import cache

# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectin_polymorphic

# from v_back.models.journal import (
#     Journal,
#     OtherRequests,
#     RebootJournal,
#     UriJournalBase,
# )
# from v_back.crud.base import CRUDBase
# from v_back.schemas.journal import (
#     JournalCreate,
#     JournalRead,
#     OtherRequestsCreate,
#     OtherRequestsRead,
#     RebootJournalCreate,
#     RebootJournalRead,
#     UriJournalBaseCreate,
#     UriJournalBaseRead,
# )


# class JournalCrud(CRUDBase[Journal, JournalRead, JournalCreate]):

#     @property
#     def _select_model(self):
#         return super()._select_model.options(
#             selectin_polymorphic(Journal, [RebootJournal, UriJournalBase])
#         )


# class RebootJournalCrud(
#     CRUDBase[RebootJournal, RebootJournalRead, RebootJournalCreate]
# ):

#     async def get_last_reboot(self, session: AsyncSession):
#         stmt = (
#             select(RebootJournal).limit(1).order_by(RebootJournal.date.desc())
#         )
#         return (await session.execute(stmt)).scalar_one_or_none()


# class UriJournalBaseCrud(
#     CRUDBase[UriJournalBase, UriJournalBaseRead, UriJournalBaseCreate]
# ):
#     pass


# class OtherRequestsCrud(
#     CRUDBase[OtherRequests, OtherRequestsRead, OtherRequestsCreate]
# ):
#     pass


# @cache
# def get_other_reqeusts_crud():
#     return OtherRequestsCrud()


# @cache
# def get_urijournal_crud():
#     return UriJournalBaseCrud()


# @cache
# def get_rebootjournal_crud():
#     return RebootJournalCrud()


# @cache
# def get_journal_crud():
#     return JournalCrud()
