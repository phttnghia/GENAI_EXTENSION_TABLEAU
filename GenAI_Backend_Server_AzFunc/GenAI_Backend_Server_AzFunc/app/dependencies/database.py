from typing import Generator, Annotated
from app.db.session import session_local
from sqlalchemy.orm import Session  # type: ignore
from fastapi import Depends


def get_db() -> Generator:
    db = session_local()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
