"""Job description CRUD: saved JDs a user can match resumes against."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.db import get_db

router = APIRouter(prefix="/jds", tags=["job-descriptions"])


def _owned_jd(db: Session, jd_id: int, user_id: int) -> models.JobDescription:
    jd = (
        db.query(models.JobDescription)
        .filter(models.JobDescription.id == jd_id, models.JobDescription.user_id == user_id)
        .first()
    )
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


@router.post("", response_model=schemas.JobDescriptionOut, status_code=status.HTTP_201_CREATED)
def create_jd(
    payload: schemas.JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    jd = models.JobDescription(
        user_id=current_user.id, title=payload.title, content_text=payload.content_text
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd


@router.get("", response_model=list[schemas.JobDescriptionOut])
def list_jds(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.JobDescription)
        .filter(models.JobDescription.user_id == current_user.id)
        .order_by(desc(models.JobDescription.created_at))
        .all()
    )


@router.get("/{jd_id}", response_model=schemas.JobDescriptionOut)
def get_jd(
    jd_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _owned_jd(db, jd_id, current_user.id)


@router.delete("/{jd_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_jd(
    jd_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    jd = _owned_jd(db, jd_id, current_user.id)
    db.delete(jd)
    db.commit()
    return None
