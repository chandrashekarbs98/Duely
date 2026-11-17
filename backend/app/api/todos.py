from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import CurrentUser, get_todo_service
from app.schemas.common import Page
from app.schemas.todo import TodoQuery, TodoRead, TodoWrite
from app.services.todo import TodoService

router = APIRouter(prefix="/todos", tags=["todos"])
Service = Annotated[TodoService, Depends(get_todo_service)]


@router.get("", response_model=Page[TodoRead])
def list_todos(
    query: Annotated[TodoQuery, Query()], user: CurrentUser, service: Service
) -> Page[TodoRead]:
    return service.list(user, query)


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
def create_todo(data: TodoWrite, user: CurrentUser, service: Service) -> TodoRead:
    return TodoRead.model_validate(service.create(user, data))


@router.get("/{todo_id}", response_model=TodoRead)
def get_todo(todo_id: int, user: CurrentUser, service: Service) -> TodoRead:
    return TodoRead.model_validate(service.get(user, todo_id))


@router.put("/{todo_id}", response_model=TodoRead)
def replace_todo(todo_id: int, data: TodoWrite, user: CurrentUser, service: Service) -> TodoRead:
    return TodoRead.model_validate(service.replace(user, todo_id, data))


@router.patch("/{todo_id}/toggle", response_model=TodoRead)
def toggle_todo(todo_id: int, user: CurrentUser, service: Service) -> TodoRead:
    return TodoRead.model_validate(service.toggle(user, todo_id))


@router.post("/{todo_id}/repeat", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
def repeat_todo(todo_id: int, user: CurrentUser, service: Service) -> TodoRead:
    return TodoRead.model_validate(service.repeat(user, todo_id))


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, user: CurrentUser, service: Service) -> None:
    service.delete(user, todo_id)
