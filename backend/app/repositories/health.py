from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class HealthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def database_ok(self) -> bool:
        try:
            self.db.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False
