"""Resume upload / listing. Files are parsed to text; the raw bytes are not stored."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.db import get_db
from app.services.pdf import extract_text_from_pdf

router = APIRouter(prefix="/resumes", tags=["resumes"])

MAX_PDF_BYTES = 5 * 1024 * 1024


def _owned_resume(db: Session, resume_id: int, user_id: int) -> models.Resume:
    resume = (
        db.query(models.Resume)
        .filter(models.Resume.id == resume_id, models.Resume.user_id == user_id)
        .first()
    )
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.post("/upload", response_model=schemas.ResumeOut, status_code=status.HTTP_201_CREATED)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    name = (file.filename or "").lower()
    if file.content_type != "application/pdf" and not name.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    data = file.file.read()
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    try:
        text = extract_text_from_pdf(data)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read PDF file")
    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in PDF")

    resume = models.Resume(user_id=current_user.id, filename=file.filename or "resume.pdf", content_text=text)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("", response_model=list[schemas.ResumeOut])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Resume)
        .filter(models.Resume.user_id == current_user.id)
        .order_by(desc(models.Resume.uploaded_at))
        .all()
    )


@router.get("/{resume_id}", response_model=schemas.ResumeOut)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _owned_resume(db, resume_id, current_user.id)
