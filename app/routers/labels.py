from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Label
from app.routers.common import commit_or_409, get_or_404
from app.schemas import LabelCreate, LabelRead, LabelUpdate

router = APIRouter(prefix="/v1/labels", tags=["labels"])


@router.get("", response_model=list[LabelRead])
def list_labels(db: Session = Depends(get_db)):
    return db.scalars(select(Label).order_by(Label.id)).all()


@router.get("/{label_id}", response_model=LabelRead)
def get_label(label_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Label, label_id)


@router.post("", response_model=LabelRead, status_code=201)
def create_label(payload: LabelCreate, db: Session = Depends(get_db)):
    label = Label(**payload.model_dump())
    db.add(label)
    commit_or_409(db, "A label with this name already exists")
    db.refresh(label)
    return label


@router.patch("/{label_id}", response_model=LabelRead)
def update_label(
    label_id: int,
    payload: LabelUpdate,
    db: Session = Depends(get_db),
):
    label = get_or_404(db, Label, label_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(label, field, value)
    commit_or_409(db, "A label with this name already exists")
    db.refresh(label)
    return label


@router.delete("/{label_id}", status_code=204)
def delete_label(label_id: int, db: Session = Depends(get_db)):
    label = get_or_404(db, Label, label_id)
    db.delete(label)
    commit_or_409(db, "Could not delete label")
    return Response(status_code=204)
