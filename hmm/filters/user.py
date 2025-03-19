from datetime import datetime

from hmm.core.filtering.sqlalchemy import Filter
from hmm.models.auth import User


class UserFilter(Filter):
    created_at__from: datetime | None = None
    created_at__till: datetime | None = None
    is_super: bool | None = None
    is_active: bool | None = None
    username__ilike: str | None = None

    class Constants(Filter.Constants):
        model = User
        search_model_fields = [
            "created_at",
            "is_super",
            "is_active",
            "username",
        ]
