from app.core import clock
from app.core.errors import NotFoundError
from app.models import Todo, User
from app.repositories.todo import TodoRepository
from app.schemas.common import Page
from app.schemas.todo import TodoQuery, TodoRead, TodoWrite
from app.services.dates import next_occurrence


class TodoService:
    def __init__(self, todos: TodoRepository) -> None:
        self.todos = todos

    def _get_owned(self, user: User, todo_id: int) -> Todo:
        todo = self.todos.get(user.id, todo_id)
        if todo is None:
            # Also the answer for "exists but belongs to someone else": never leak existence.
            raise NotFoundError("Todo not found.")
        return todo

    def list(self, user: User, query: TodoQuery) -> Page[TodoRead]:
        items, total = self.todos.search(user.id, query)
        return Page[TodoRead](
            items=[TodoRead.model_validate(t) for t in items],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    def get(self, user: User, todo_id: int) -> Todo:
        return self._get_owned(user, todo_id)

    def create(self, user: User, data: TodoWrite) -> Todo:
        return self.todos.create(user.id, data.model_dump())

    def replace(self, user: User, todo_id: int, data: TodoWrite) -> Todo:
        todo = self._get_owned(user, todo_id)
        return self.todos.update(todo, data.model_dump())

    def toggle(self, user: User, todo_id: int) -> Todo:
        todo = self._get_owned(user, todo_id)
        done = not todo.completed
        return self.todos.update(
            todo, {"completed": done, "completed_at": clock.now() if done else None}
        )

    def repeat(self, user: User, todo_id: int) -> Todo:
        """Copy the todo to its next period: tomorrow / next month / next year."""
        todo = self._get_owned(user, todo_id)
        base = todo.due_date or clock.today()
        return self.todos.create(
            user.id,
            {
                "title": todo.title,
                "description": todo.description,
                "period": todo.period,
                "priority": todo.priority,
                "category": todo.category,
                "due_date": next_occurrence(base, todo.period),
            },
        )

    def delete(self, user: User, todo_id: int) -> None:
        self.todos.delete(self._get_owned(user, todo_id))
