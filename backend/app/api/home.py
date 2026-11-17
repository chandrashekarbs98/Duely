from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, get_home_service
from app.schemas.dashboard import HomeResponse
from app.services.home import HomeService

router = APIRouter(tags=["home"])


@router.get("/home", response_model=HomeResponse)
def home(
    user: CurrentUser, service: Annotated[HomeService, Depends(get_home_service)]
) -> HomeResponse:
    return service.home(user)
