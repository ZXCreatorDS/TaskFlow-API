from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment
from app.routers.common import commit_or_409, get_or_404
from app.schemas import CommentCreate, CommentRead, CommentUpdate

router = APIRouter(prefix="/v1/comments", tags=["comments"])


@router.get("", response_model=list[CommentRead])
def list_comments(
    task_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Comment).order_by(Comment.id)
    if task_id is not None:
        stmt = stmt.where(Comment.task_id == task_id)
    return db.scalars(stmt).all()


@router.get("/{comment_id}", response_model=CommentRead)
def get_comment(comment_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Comment, comment_id)


@router.post("", response_model=CommentRead, status_code=201)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db)):
    comment = Comment(**payload.model_dump())
    db.add(comment)
    commit_or_409(db, "Task or author does not exist")
    db.refresh(comment)
    return comment


@router.patch("/{comment_id}", response_model=CommentRead)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
):
    comment = get_or_404(db, Comment, comment_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(comment, field, value)
    commit_or_409(db, "Task or author does not exist")
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}", status_code=204)
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = get_or_404(db, Comment, comment_id)
    db.delete(comment)
    commit_or_409(db, "Could not delete comment")
    return Response(status_code=204)
