"""Application entrypoint: wiring, middleware, lifespan."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.db import Base, engine
from app.rate_limit import limiter
from app.routers import analysis, auth, job_descriptions, resumes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Scaffold convenience: create tables on startup.
    # Production path: replace with Alembic migrations (see README roadmap).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Resume Analyzer API", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(job_descriptions.router)
app.include_router(analysis.router)

# Serve the frontend at /app (same origin, no CORS juggling in the demo).
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
