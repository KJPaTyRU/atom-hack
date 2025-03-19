from collections import namedtuple
from typing import Any, Callable, TypeAlias
from warnings import warn
from loguru import logger

from sqlalchemy.sql.selectable import Select

from .base import BaseFilterModel

prepared_notify_filters = namedtuple(
    "prepared_notify_filters", ["where", "having"]
)


def _backward_compatible_value_for_like_and_ilike(value: str):
    """Add % if not in value to be backward compatible.

    Args:
        value (str): The value to filter.

    Returns:
        Either the unmodified value if a percent sign is present, the value
        wrapped in % otherwise to preserve
        current behavior.
    """
    if "%" not in value:
        warn(
            "You must pass the % character explicitly to use the like and"
            " ilike operators.",
            DeprecationWarning,
            stacklevel=2,
        )
        value = f"%{value}%"
    return value


MethodAndValued: TypeAlias = tuple[str, Any]
GetMethodAndValued: TypeAlias = Callable[[str], MethodAndValued]
FrontMethod: TypeAlias = str
_orm_operator_transformer: dict[FrontMethod, GetMethodAndValued] = {
    "eq": lambda value: ("__eq__", value),
    "neq": lambda value: ("__ne__", value),
    "gt": lambda value: ("__gt__", value),
    "gte": lambda value: ("__ge__", value),
    "isnull": lambda value: (
        ("is_", None) if value is True else ("is_not", None)
    ),
    "lt": lambda value: ("__lt__", value),
    "lte": lambda value: ("__le__", value),
    "from": lambda value: ("__ge__", value),
    "till": lambda value: ("__le__", value),
    "like": lambda value: (
        "like",
        _backward_compatible_value_for_like_and_ilike(value),
    ),
    "ilike": lambda value: (
        "ilike",
        _backward_compatible_value_for_like_and_ilike(value),
    ),
    "not": lambda value: ("is_not", value),
    "in": lambda value: ("in_", value),
    "not_in": lambda value: ("not_in", value),
}


class Filter(BaseFilterModel):
    """Base filter for orm related filters.

    All children must set:
        ```python
        class Constants(Filter.Constants):
            model = MyModel
        ```

    It can handle regular field names and Django style operators.

    Example:
        ```python
        class MyModel:
            id: PrimaryKey()
            name: StringField(nullable=True)
            count: IntegerField()
            created_at: DatetimeField()

        class MyModelFilter(Filter):
            id: Optional[int]
            id__in: Optional[str]
            count: Optional[int]
            count__lte: Optional[int]
            created_at__gt: Optional[datetime]
            name__isnull: Optional[bool]
    """

    def parse_field(self, cur_field: str) -> tuple[str, GetMethodAndValued]:
        splits = cur_field.rsplit("__", 1)
        if len(splits) == 1:
            return (
                splits[0],
                _orm_operator_transformer["eq"],
            )  # default operator
        return splits[0], _orm_operator_transformer[splits[1]]

    def simple_filter(
        self, stmt: Select, cur_field: str, filtering_fields: dict[str, Any]
    ) -> Select:
        # Reduse func calls with simple copying this code to the call place
        field_name, mfunc = self.parse_field(cur_field)
        operation, value = mfunc(filtering_fields[cur_field])

        func_filter = getattr(self, f"criteria_{cur_field}", None)
        if func_filter is not None:
            stmt = stmt.filter(func_filter(value))
        elif field_name in self.Constants.search_model_fields:
            model_column = getattr(self.Constants.model, field_name)
            stmt = stmt.filter(getattr(model_column, operation)(value))
        return stmt

    def filter(self, stmt: Select):
        filtering_fields = self.filtering_fields
        logger.debug("Filtering fields: {}", filtering_fields)
        for origfield_name in filtering_fields.keys():
            filter_field = getattr(self, origfield_name)
            if isinstance(filter_field, Filter):
                stmt = filter_field.filter(stmt)
            else:
                stmt = self.simple_filter(
                    stmt, origfield_name, filtering_fields
                )
        return stmt
