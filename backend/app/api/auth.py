from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.config import get_settings
from app.core.deps import CurrentUser, get_auth_service
from app.models import User
from app.schemas.auth import LoginRequest, MeResponse, RegisterRequest, UserRead, UserUpdate
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
Service = Annotated[AuthService, Depends(get_auth_service)]


def _set_auth_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.jwt_expire_hours * 3600,
        httponly=True,  # JavaScript cannot read it, so an XSS bug cannot steal it
        secure=settings.is_production,  # only sent over HTTPS in production
        samesite="lax",  # not sent on cross-site POSTs: basic CSRF protection
        path="/",
    )


def _me(user: User) -> MeResponse:
    return MeResponse(
        **UserRead.model_validate(user).model_dump(), currency=get_settings().currency
    )


@router.post("/register", response_model=MeResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, response: Response, service: Service) -> MeResponse:
    user, token = service.register(data)
    _set_auth_cookie(response, token)
    return _me(user)


@router.post("/login", response_model=MeResponse)
def login(data: LoginRequest, response: Response, service: Service) -> MeResponse:
    user, token = service.login(data)
    _set_auth_cookie(response, token)
    return _me(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        settings.auth_cookie_name,
        path="/",
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser) -> MeResponse:
    return _me(user)


@router.patch("/me", response_model=MeResponse)
def update_me(data: UserUpdate, user: CurrentUser, service: Service) -> MeResponse:
    return _me(service.update_profile(user, data))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: CurrentUser, response: Response, service: Service) -> None:
    service.delete_account(user)
    logout(response)
