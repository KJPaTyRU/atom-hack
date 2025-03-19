from fastapi import Query
import sqlalchemy as sa
from pydantic import PositiveInt

from hmm.config import get_settings


def validate_unsigned_number(v: int):
    if v <= 0:
        raise ValueError("Value error (v <= 0)")
    return v


class Paginator:
    """Class for list pagination logic"""

    MAX_LIMIT: PositiveInt = get_settings().app.PAGINATOR_MAX_LIMIT
    INIT_PAGE: PositiveInt = 1

    def __init__(
        self, MAX_LIMIT: PositiveInt = get_settings().app.PAGINATOR_MAX_LIMIT
    ) -> None:
        self.MAX_LIMIT = validate_unsigned_number(MAX_LIMIT)

    def __call__(
        self,
        limit: PositiveInt | None = None,
        page: PositiveInt | None = INIT_PAGE,
    ):
        self._limit = limit
        self.page = page
        return self

    @property
    def limit(self):
        if self._limit is None or self.page is None:
            return None
        return min(self._limit, self.get_max_limit())

    def get_max_limit(self):
        """returns max pagination limit.
        Override this method in order to change how
        the maximum limit value is obtained.

        Returns:
            int: maximum limit value
        """
        return self.MAX_LIMIT

    @property
    def offset(self):
        return (self.page - 1) * self.limit

    def paginate(self, qs: sa.Select):
        qs2 = qs
        if self.limit is not None:
            qs2 = qs2.limit(self.limit).offset(self.offset)
        qs_count = sa.select(sa.func.count("*")).select_from(
            qs.order_by(None).subquery("count_sq")
        )
        return qs2, qs_count


class RightBoarder(Paginator):
    """it's like a paginator but w/o page (1 always = 0 offset)
    and force required limit"""

    def __call__(self, count: PositiveInt):
        self._limit = count
        self.page = 1
        return self


class DisabledPaginator(Paginator):
    """no allowed to paginate"""

    def __call__(self):
        self._limit = None
        return self


def default_paginator(
    limit: PositiveInt | None = Query(None), page: PositiveInt = Query(1)
):
    return Paginator()(limit, page)


def paginator100(
    limit: PositiveInt | None = Query(None), page: PositiveInt = Query(1)
):
    return Paginator(100)(limit, page)


def disabled_paginator():
    return DisabledPaginator()
