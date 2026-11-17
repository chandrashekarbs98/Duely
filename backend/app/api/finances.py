from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.core import clock
from app.core.deps import CurrentUser, get_finance_service
from app.schemas.common import Page
from app.schemas.finance import (
    FinanceFilters,
    FinanceQuery,
    FinanceRead,
    FinanceStats,
    FinanceWrite,
    StatsQuery,
)
from app.services.finance import FinanceService

router = APIRouter(prefix="/finances", tags=["finances"])
Service = Annotated[FinanceService, Depends(get_finance_service)]


@router.get("", response_model=Page[FinanceRead])
def list_entries(
    query: Annotated[FinanceQuery, Query()], user: CurrentUser, service: Service
) -> Page[FinanceRead]:
    return service.list(user, query)


@router.post("", response_model=FinanceRead, status_code=status.HTTP_201_CREATED)
def create_entry(data: FinanceWrite, user: CurrentUser, service: Service) -> FinanceRead:
    return FinanceRead.model_validate(service.create(user, data))


# Fixed paths must be declared before "/{entry_id}", or "stats" would be read as an id.
@router.get("/stats", response_model=FinanceStats)
def stats(
    query: Annotated[StatsQuery, Query()], user: CurrentUser, service: Service
) -> FinanceStats:
    return service.stats(user, query)


@router.get("/export.csv", response_class=Response)
def export_csv(
    filters: Annotated[FinanceFilters, Query()], user: CurrentUser, service: Service
) -> Response:
    filename = f"finances-{clock.today().isoformat()}.csv"
    return Response(
        content=service.export_csv(user, filters),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{entry_id}", response_model=FinanceRead)
def get_entry(entry_id: int, user: CurrentUser, service: Service) -> FinanceRead:
    return FinanceRead.model_validate(service.get(user, entry_id))


@router.put("/{entry_id}", response_model=FinanceRead)
def replace_entry(
    entry_id: int, data: FinanceWrite, user: CurrentUser, service: Service
) -> FinanceRead:
    return FinanceRead.model_validate(service.replace(user, entry_id, data))


@router.patch("/{entry_id}/pay", response_model=FinanceRead)
def mark_paid(entry_id: int, user: CurrentUser, service: Service) -> FinanceRead:
    return FinanceRead.model_validate(service.mark_paid(user, entry_id))


@router.post("/{entry_id}/repeat", response_model=FinanceRead, status_code=status.HTTP_201_CREATED)
def repeat_entry(entry_id: int, user: CurrentUser, service: Service) -> FinanceRead:
    return FinanceRead.model_validate(service.repeat(user, entry_id))


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, user: CurrentUser, service: Service) -> None:
    service.delete(user, entry_id)
