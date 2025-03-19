from typing import TYPE_CHECKING, Any, Iterable, Optional, Type, Union

from fastapi import Depends
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from sqlalchemy import Select


if TYPE_CHECKING:
    from cr.models.base import Base
# rewriting of fastapi-filter for pydantic V2


class BaseFilterModel(BaseModel, extra="forbid"):
    class Constants:  # pragma: no cover
        model: "Type | type[Base]"
        search_model_fields: Iterable[str] = []
        search_field_name: str = "search"
        prefix: str

    def filter(self, stmt: Select) -> Select:  # pragma: no cover
        raise NotImplementedError()

    def filter_relative(self) -> dict[str, list]:  # pragma: no cover
        pass

    @property
    def filtering_fields(self):
        fields = self.model_dump(exclude_none=True, exclude_unset=True)
        return fields

    def sort(self, stmt: Select) -> Select:  # pragma: no cover
        raise NotImplementedError()


def _get_annotation(name: str, field: FieldInfo):
    annon = field.annotation
    if not field.is_required():
        annon = annon | None
    if name.endswith("__in") or name.endswith("__not_in"):
        annon = annon | list[field.annotation]
    return annon


def _list_to_str_fields(Filter: Type[BaseFilterModel]):  # pragma: no cover
    ret: dict[str, tuple[Union[object, Type], Optional[FieldInfo]]] = {}
    for name, f in Filter.model_fields.items():
        annotation = _get_annotation(name, f)
        ret[name] = (annotation, f)
    return ret


def FilterDepends(  # pragma: no cover
    Filter: Type[BaseFilterModel],  # pragma: no cover
    *,
    by_alias: bool = False,
    use_cache: bool = True,
) -> Any:
    fields = _list_to_str_fields(Filter)
    GeneratedFilter: Type[BaseFilterModel] = create_model(
        Filter.__class__.__name__, **fields
    )

    class FilterWrapper(GeneratedFilter):  # type: ignore[misc,valid-type]
        def filter(self: "FilterWrapper | BaseFilterModel", *args, **kwargs):
            d = self.model_dump(mode="python", by_alias=by_alias)
            original_filter = Filter.model_construct(**d)
            return original_filter.filter(*args, **kwargs)

    return Depends(FilterWrapper, use_cache=use_cache)
