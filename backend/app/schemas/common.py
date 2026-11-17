from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# Money in requests: exact decimal, positive, at most 2 decimal places, fits NUMERIC(12,2).
# Pydantic rejects 10.999 instead of silently rounding it.
Money = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class Page[T](BaseModel):
    """A page of results plus the total, so the UI can draw pagination."""

    items: list[T]
    total: int
    limit: int
    offset: int


class ORMModel(BaseModel):
    # from_attributes lets Pydantic read straight from SQLAlchemy objects.
    model_config = ConfigDict(from_attributes=True)


class InputModel(BaseModel):
    # Trim surrounding spaces and reject unknown fields, so typos fail loudly.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
