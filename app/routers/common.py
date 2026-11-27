import logging
from typing import TypeVar

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT")


def get_or_404(db: Session, model: type[ModelT], obj_id: int) -> ModelT:
    obj = db.get(model, obj_id)
    if obj is None:
        logger.warning("%s %s not found", model.__name__, obj_id)
        raise HTTPException(
            status_code=404,
            detail=f"{model.__name__} {obj_id} not found",
        )
    return obj


def commit_or_409(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Integrity conflict: %s", detail)
        raise HTTPException(status_code=409, detail=detail) from exc
