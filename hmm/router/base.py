import asyncio
import datetime
from typing import Any, Callable, Sequence, TypeVar
from fastapi import Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from hmm.crud.base import CRUDBase
from hmm.models.base import Base, BoundDbModel
from hmm.schemas.base import OrmModel
from hmm.core.filtering.base import BaseFilterModel
from hmm.core.ordering import Ordering
from hmm.core.paginator import Paginator

BaseModelT = TypeVar("BaseModelT", bound=OrmModel)


ListSchema = TypeVar("ListSchema", bound=BaseModel)
ConvertedSchema = TypeVar("ConvertedSchema", bound=BaseModel)

MIN_DATE_BOUND_HEADER = "x-min-date-from"
MAX_DATE_BOUND_HEADER = "x-max-date-till"
TOTAL_COUNT = "x-total-count"


def base_create_converter(
    data: ListSchema, schema: ConvertedSchema, **kwargs
) -> ConvertedSchema:
    return schema(**data.model_dump(), **kwargs)


class BaseHeaderDate(OrmModel):
    x_max_date: datetime.datetime | None = Field(
        serialization_alias=MAX_DATE_BOUND_HEADER
    )
    x_min_date: datetime.datetime | None = Field(
        serialization_alias=MIN_DATE_BOUND_HEADER
    )

    @property
    def headers(self):
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)


async def set_bounds_response(
    session: AsyncSession,
    response: Response,
    model: type[BoundDbModel],
    **kwargs,
) -> None:
    query = model.date_bounds(**kwargs)
    boarders = (await session.execute(query)).first()
    headers = BaseHeaderDate.model_validate(boarders).headers
    response.headers.update(headers)


def _obj_to_response(
    obj: Sequence[Base],
    response_type: BaseModelT,
    response: Response,
    **kwargs,
) -> dict:
    return [response_type.model_validate(oi).to_front() for oi in obj]


async def execute_mode(session: AsyncSession, stmt: Select, mode: bool):
    """Just a simple function for SQLAlchem executing process."""
    if mode:
        data = (await session.execute(stmt)).scalars().unique().all()
    else:
        data = (await session.execute(stmt)).all()
    return data


async def base_model_get(
    response: Response,
    session: AsyncSession,
    crud: CRUDBase,
    pagination: Paginator,
    query_filter: BaseFilterModel | None,
    ordering: Ordering | None,
    query: Select,
    response_schema: type[BaseModelT] | None = None,
    add_total_count_header: bool = True,
    add_bound_date_header: bool = False,
    obj_to_response: (
        Callable[[Sequence[Base], type[BaseModelT], Response, Any], BaseModelT]
        | None
    ) = _obj_to_response,  # type: ignore
    patch_query=None,
    _bound_response_kwargs: dict[str, Any] | None = None,
    execute_scalars: bool = True,
):
    if patch_query:
        query = patch_query(query)
    if query_filter:
        query = query_filter.filter(query)
    if ordering:
        query = ordering.sort(query)
    qs, c = pagination.paginate(query)
    data = await execute_mode(session, qs, execute_scalars)
    if add_total_count_header:
        size = (await session.execute(c)).scalar()
        response.headers.update({TOTAL_COUNT: str(size)})
    if add_bound_date_header:
        if crud is None:
            raise ValueError(
                "'crud' must not be None with 'add_bound_date_header' flag"
            )
        if _bound_response_kwargs is None:
            _bound_response_kwargs = {}
        await set_bounds_response(
            session, response, crud.model, **_bound_response_kwargs
        )
    if obj_to_response and response_schema is not None:
        data = JSONResponse(
            await asyncio.to_thread(
                obj_to_response, data, response_schema, response
            ),
            headers=response.headers,
        )
    return data
