from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.core.deps import get_health_repository
from app.repositories.health import HealthRepository
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    response: Response, repo: Annotated[HealthRepository, Depends(get_health_repository)]
) -> HealthResponse:
    """Used by the host to decide whether this instance is healthy."""
    if repo.database_ok():
        return HealthResponse(status="ok", database="ok")
    response.status_code = 503
    return HealthResponse(status="degraded", database="unreachable")
