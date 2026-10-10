# Resume Analyzer

Production-style SaaS that scores resumes ATS-style, matches them against job
descriptions, and gives actionable feedback. Upload a PDF resume, save JDs,
get a 0–100 match score plus concrete suggestions. Built with FastAPI,
Postgres, JWT auth, tests, CI and Docker.

## Architecture

```
                    ┌─────────────┐
                    │  Frontend   │  vanilla JS SPA (served at /app)
                    └──────┬──────┘
                           │  REST + JWT
                    ┌──────▼──────┐
                    │   FastAPI   │  routers: auth / resumes / analysis
                    │             │  services: pdf parsing, heuristic + LLM analysis
                    └──────┬──────┘
                           │  SQLAlchemy
                    ┌──────▼──────┐
                    │  Postgres   │  users → resumes → analyses
                    └─────────────┘
```

## Quickstart (Docker)

```bash
cp .env.example .env   # then set a real JWT_SECRET_KEY
docker compose up --build
```

- API docs: http://localhost:8000/docs
- Frontend: http://localhost:8000/app
- Health: http://localhost:8000/health

## Local dev (no Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload        # uses sqlite dev.db by default
pytest -q                            # runs the test suite
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./dev.db` | SQLAlchemy URL (Postgres in Docker/CI prod) |
| `JWT_SECRET_KEY` | `dev-secret-change-me` | **Must** be changed in production |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |
| `OPENAI_API_KEY` | _(empty)_ | Optional: enriches feedback with an LLM call |

## API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | – | Create account |
| POST | `/auth/login` | – | OAuth2 password flow → JWT |
| GET | `/auth/me` | JWT | Current user |
| POST | `/resumes/upload` | JWT | Upload PDF resume (max 5MB) |
| GET | `/resumes` | JWT | List your resumes |
| GET | `/resumes/{id}` | JWT | Get one resume (metadata) |
| POST | `/resumes/{id}/analyze` | JWT | Run ATS analysis (10/min rate-limited) |
| GET | `/resumes/{id}/analyses` | JWT | Analysis history |
| POST | `/jds` | JWT | Save a job description |
| GET | `/jds` | JWT | List your job descriptions |
| GET | `/jds/{id}` | JWT | Get one job description |
| DELETE | `/jds/{id}` | JWT | Delete a job description |
| POST | `/resumes/{id}/match` | JWT | Match resume vs JD (10/min rate-limited) |
| POST | `/resumes/{id}/rewrite` | JWT | Rewrite weak bullets + draft JD-tailored bullets |
| POST | `/resumes/{id}/cover-letter` | JWT | Generate tailored cover letter |

Interactive docs at `/docs` (Swagger) once the server is running.

## Tests

```bash
pytest -q
```

Tests run against an isolated SQLite DB (`test.db`, created and removed by the
test session). PDF parsing is stubbed so tests stay deterministic.

## Project structure

```
app/
  main.py          # wiring, CORS, rate limiting, lifespan
  config.py        # env-based settings
  db.py            # engine + session dependency
  models.py        # User / Resume / Analysis
  schemas.py       # pydantic API contract
  auth.py          # bcrypt + JWT
  rate_limit.py    # slowapi limiter
  routers/         # auth, resumes, analysis endpoints
  services/        # pdf.py (text extraction), analyzer.py (scoring)
frontend/          # vanilla JS SPA
tests/             # pytest suite
.github/workflows/ # CI: install + pytest on every push
```

## Roadmap (to make it truly industrial)

- Alembic migrations instead of `create_all`
- Background job queue (Celery/Redis) for analysis
- Object storage (S3) for uploaded PDFs
- Refresh tokens + email verification
- Frontend framework + component tests
