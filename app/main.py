from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import comments, labels, projects, tasks, users

app = FastAPI(
    title="TaskFlow API",
    description="REST API для управления задачами команды.",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(labels.router)
app.include_router(tasks.router)
app.include_router(comments.router)


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        ) from exc
    return {"status": "ok"}
