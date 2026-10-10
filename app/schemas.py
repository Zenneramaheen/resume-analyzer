"""Pydantic request/response schemas (API contract)."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Resumes ---
class ResumeOut(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# --- Analysis ---
class AnalyzeRequest(BaseModel):
    target_role: str = Field(default="software engineer", max_length=120)


# --- Job descriptions ---
class JobDescriptionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content_text: str = Field(min_length=20)


class JobDescriptionOut(BaseModel):
    id: int
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- JD matching ---
class MatchRequest(BaseModel):
    job_description_id: int


class MatchOut(BaseModel):
    id: int
    resume_id: int
    score: int
    summary: str
    suggestions: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CoverLetterRequest(BaseModel):
    job_description_id: int
    company_name: str = Field(default="", max_length=200)


class CoverLetterOut(BaseModel):
    id: int
    resume_id: int
    letter_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RewriteRequest(BaseModel):
    job_description_id: int | None = None


class RewriteItem(BaseModel):
    original: str | None = None
    suggestion: str
    reason: str


class RewriteOut(BaseModel):
    id: int
    resume_id: int
    rewrites: list[RewriteItem]
    created_at: datetime


class AnalysisOut(BaseModel):
    id: int
    resume_id: int
    score: int
    summary: str
    suggestions: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
