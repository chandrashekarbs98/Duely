from fastapi import APIRouter

from app.api import auth, finances, health, home, reminders, todos

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(todos.router)
api_router.include_router(finances.router)
api_router.include_router(home.router)
api_router.include_router(reminders.router)
