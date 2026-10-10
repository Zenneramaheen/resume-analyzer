"""Analysis endpoints: run ATS-style analysis on an owned resume, view history."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.db import get_db
from app.rate_limit import limiter
from app.services.analyzer import analyze_resume_text
from app.services.cover_letter import generate_cover_letter
from app.services.matcher import match_resume_to_jd
from app.services.rewriter import rewrite_bullets

router = APIRouter(prefix="/resumes", tags=["analysis"])


def _owned_resume(db: Session, resume_id: int, user_id: int) -> models.Resume:
    resume = (
        db.query(models.Resume)
        .filter(models.Resume.id == resume_id, models.Resume.user_id == user_id)
        .first()
    )
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.post("/{resume_id}/analyze", response_model=schemas.AnalysisOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def analyze_resume(
    request: Request,
    resume_id: int,
    payload: schemas.AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    resume = _owned_resume(db, resume_id, current_user.id)
    result = analyze_resume_text(resume.content_text, target_role=payload.target_role)
    analysis = models.Analysis(
        resume_id=resume.id,
        score=result["score"],
        summary=result["summary"],
        suggestions=result["suggestions"],
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@router.get("/{resume_id}/analyses", response_model=list[schemas.AnalysisOut])
def analysis_history(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    resume = _owned_resume(db, resume_id, current_user.id)
    return (
        db.query(models.Analysis)
        .filter(models.Analysis.resume_id == resume.id)
        .order_by(desc(models.Analysis.created_at))
        .all()
    )


@router.post("/{resume_id}/match", response_model=schemas.MatchOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def match_against_jd(
    request: Request,
    resume_id: int,
    payload: schemas.MatchRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Score a resume against a saved job description (keyword coverage)."""
    resume = _owned_resume(db, resume_id, current_user.id)
    jd = (
        db.query(models.JobDescription)
        .filter(
            models.JobDescription.id == payload.job_description_id,
            models.JobDescription.user_id == current_user.id,
        )
        .first()
    )
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")

    result = match_resume_to_jd(resume.content_text, jd.content_text)
    analysis = models.Analysis(
        resume_id=resume.id,
        kind="jd_match",
        score=result["score"],
        summary=result["summary"],
        suggestions=result["suggestions"],
        details={
            "job_description_id": jd.id,
            "matched_keywords": result["matched_keywords"],
            "missing_keywords": result["missing_keywords"],
        },
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return {
        "id": analysis.id,
        "resume_id": resume.id,
        "score": analysis.score,
        "summary": analysis.summary,
        "suggestions": analysis.suggestions,
        "matched_keywords": result["matched_keywords"],
        "missing_keywords": result["missing_keywords"],
        "created_at": analysis.created_at,
    }


def _owned_jd(db: Session, jd_id: int, user_id: int) -> models.JobDescription:
    jd = (
        db.query(models.JobDescription)
        .filter(
            models.JobDescription.id == jd_id,
            models.JobDescription.user_id == user_id,
        )
        .first()
    )
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


@router.post("/{resume_id}/rewrite", response_model=schemas.RewriteOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def rewrite_resume(
    request: Request,
    resume_id: int,
    payload: schemas.RewriteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Rewrite weak bullets and draft tailored bullets for JD keywords."""
    resume = _owned_resume(db, resume_id, current_user.id)
    missing: list[str] = []
    jd_id = payload.job_description_id
    if jd_id is not None:
        jd = _owned_jd(db, jd_id, current_user.id)
        missing = match_resume_to_jd(resume.content_text, jd.content_text)["missing_keywords"]

    rewrites = rewrite_bullets(resume.content_text, missing)
    analysis = models.Analysis(
        resume_id=resume.id,
        kind="rewrite",
        score=0,
        summary=f"Generated {len(rewrites)} rewrite suggestions.",
        suggestions=[r["suggestion"] for r in rewrites],
        details={"job_description_id": jd_id, "rewrites": rewrites},
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return {
        "id": analysis.id,
        "resume_id": resume.id,
        "rewrites": rewrites,
        "created_at": analysis.created_at,
    }


@router.post("/{resume_id}/cover-letter", response_model=schemas.CoverLetterOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def make_cover_letter(
    request: Request,
    resume_id: int,
    payload: schemas.CoverLetterRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generate a tailored cover letter for a resume + job description."""
    resume = _owned_resume(db, resume_id, current_user.id)
    jd = _owned_jd(db, payload.job_description_id, current_user.id)

    matched = match_resume_to_jd(resume.content_text, jd.content_text)
    letter = generate_cover_letter(
        resume.content_text,
        jd.content_text,
        role=jd.title,
        company=payload.company_name,
        matched_keywords=matched["matched_keywords"],
    )
    analysis = models.Analysis(
        resume_id=resume.id,
        kind="cover_letter",
        score=0,
        summary=f"Cover letter generated for '{jd.title}'.",
        suggestions=[],
        details={"job_description_id": jd.id, "letter_text": letter},
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return {
        "id": analysis.id,
        "resume_id": resume.id,
        "letter_text": letter,
        "created_at": analysis.created_at,
    }
