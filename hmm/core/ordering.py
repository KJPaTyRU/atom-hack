from enum import Enum
import re
from typing import TYPE_CHECKING, Annotated, Any, Iterable
from fastapi import Depends, Query, HTTPException

import sqlalchemy as sa

if TYPE_CHECKING:
    from hmm.models.base import Base


SORT_BY_TEMPALTE = re.compile(r"^(?P<order>[+-])(?P<field>[\w]+)$")
QueryListOfString = Annotated[
    list[str],
    Query(
        description=(
            "Последовательность полей, по которой будет происходить сортировка"
            " выходного результата. Если в начале поля стоит `-`, то"
            " сортировка будет происходить в порядке *УБЫВАНИЯ*;  Если в"
            " начале поля стоит `+` - *ВОЗРАСТАНИЯ*"
        )
    ),
]


def _get_fields(
    model: "type[Base]",
    order_fields: Iterable[str] | None = None,
    default_order_fields: Iterable[str] | None = None,
):
    if order_fields is not None and default_order_fields is not None:
        for dofi in default_order_fields:
            if dofi[1:] not in order_fields:
                raise ValueError(
                    "Items in 'default_order_fields' must be fields from"
                    " 'order_fields'"
                )
        return order_fields, _sort(default_order_fields, order_fields)
    _fields = model.order_fields()
    _default_sort = _sort(model.default_order_fields(), _fields)
    return set(_fields), _default_sort


def _sort(sort_by: list[Enum | str], allowed_fields: set[str]):
    sort_by = [si.value if isinstance(si, Enum) else si for si in sort_by]
    ret_list = []
    field_set = set()
    for s in sort_by:
        if s == "--":
            # Swagger skip
            continue
        M = SORT_BY_TEMPALTE.match(s)
        if M is None:
            raise HTTPException(
                status_code=400, detail=f"Incorrect sort field syntax: {s}"
            )

        tmp = M.groupdict()
        if (field := tmp["field"]) in allowed_fields:
            if field in field_set:
                raise HTTPException(
                    status_code=400,
                    detail=f"the sort {field=} occurs several times",
                )
            field_set.add(field)
            ret_list.append(tmp)
        else:
            raise HTTPException(
                status_code=400,
                detail=f'It is forbidden to sort by the "{field}" field',
            )
    return ret_list


def _ordered_map_to_list(map: list[dict]):
    return [mi["order"] + mi["field"] for mi in map]


def OrderDepends(order: "Ordering"):
    _model = order._model
    _fields, _default_sort = _get_fields(
        _model,
        order_fields=order._order_fields,
        default_order_fields=order._default_order_fields,
    )
    fs = {}
    cls = order.__class__
    for operator in cls.ACS_DESC_CONVERT:
        for fi in _fields:
            order_operator = operator + fi
            fs[order_operator] = order_operator
    OrderEnum = Enum(
        f"{cls.__name__}_{_model.__class__.__name__}_OrderEnum", fs
    )
    if order._enable_docs:

        def order_func(
            sort_by: list[OrderEnum] = Query(  # type: ignore
                _ordered_map_to_list(_default_sort)
            ),
        ):
            res = cls(_model)
            res.fields = _fields
            res._default_sort = _default_sort
            return res(sort_by)

    else:

        def order_func():
            res = cls(_model)
            res.fields = _fields
            res._default_sort = _default_sort
            return res()

    return Depends(order_func, use_cache=True)


class Ordering:
    ACS_DESC_CONVERT = {"-": sa.desc, "+": sa.asc}
    ACS_DESC_TEXT_CONVERT = {"-": "DESC", "+": "ASC"}
    _enable_docs = True

    def __init__(
        self,
        model: "type[Base]",  # hmm... Add None
        *,
        order_fields: Iterable[str] | None = None,
        default_order_fields: Iterable[str] | None = None,
    ) -> None:
        self._model = model
        self.sort_by: list[dict[str, str | Any]] = []
        self._default_sort: list[dict[str, str | Any]]
        self._order_fields = order_fields
        self._default_order_fields = default_order_fields
        self.fields: set[str] = set()

    def __call__(self, sort_by: QueryListOfString = []):
        self.sort_by = _sort(sort_by, self.fields) or self._default_sort
        return self

    def _build_order_fields(self, sort_by: Iterable[dict]):
        end = []
        for si in sort_by:
            if hasattr(self._model, si["field"]):
                end.append(
                    self.ACS_DESC_CONVERT[si["order"]](
                        getattr(self._model, si["field"])
                    )
                )
                continue
            if si["field"] not in self.fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incorrect sort field: {si['field']}",
                )
            end.append(
                sa.text(
                    f"{si['field']} {self.ACS_DESC_TEXT_CONVERT[si['order']]}"
                )
            )
        return end

    def _ordering(self, qs: sa.Select, sort_by: list[dict]):
        return qs.order_by(*self._build_order_fields(sort_by))

    def sort(self, qs: sa.Select):
        if not self.sort_by:
            return qs

        """Calling this method multiple times is equivalent to calling
        it once with all the clauses concatenated. All existing ORDER BY
        criteria may be cancelled by passing None by itself. New ORDER BY
        criteria may then be added by invoking _orm.Query.order_by again, e.g.:

        # will erase all ORDER BY and ORDER BY new_col alone
        stmt = stmt.order_by(None).order_by(new_col)
        """
        return self._ordering(qs, self.sort_by)

    @property
    def description(self):
        sort_columns = "__Sort columns__:  \n"
        sort_columns += "\n".join([f" - {field}  " for field in self.fields])

        default_sort = "__Default sort__:  \n"
        default_sort += "\n".join(
            [f" - {raw_sort}" for raw_sort in self._default_sort]
        )

        return sort_columns + "\n\n" + default_sort
