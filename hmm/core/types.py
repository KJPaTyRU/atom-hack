from typing import Annotated

from pydantic import Field

TaskLvl = Annotated[int, Field(ge=1, le=3)]
ManaFloatType = Annotated[float, Field(gte=0)]
