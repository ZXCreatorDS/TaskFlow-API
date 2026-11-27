import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.logging_config import configure_logging
from app.routers import comments, labels, projects, tasks, users

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("TaskFlow API starting")
    yield
    logger.info("TaskFlow API stopped")


app = FastAPI(
    title="TaskFlow API",
    description="REST API для управления задачами команды.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(labels.router)
app.include_router(tasks.router)
app.include_router(comments.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(
        "Request: %s %s query=%s",
        request.method,
        request.url.path,
        dict(request.query_params),
    )

    try:
        response = await call_next(request)
    except Exception:
        logger.critical(
            "Unhandled exception: %s %s",
            request.method,
            request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    if response.status_code >= 500:
        logger.error(
            "%s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
        )
    elif response.status_code >= 400:
        logger.warning(
            "%s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
        )
    else:
        logger.info(
            "%s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
        )

    return response


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
    except SQLAlchemyError as exc:
        logger.error("Database health check failed", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        ) from exc
    logger.info("Health check passed")
    return {"status": "ok"}
