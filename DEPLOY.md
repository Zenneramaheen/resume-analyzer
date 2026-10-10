# Deploying Resume Analyzer — ship-it guide

Your repo is already deploy-shaped: one service serves the API **and** the
frontend (at `/app`, same origin — no CORS juggling), tables auto-create on
startup, and everything works without an OpenAI key. Two small fixes landed
today so PaaS deploys just work:

- `Dockerfile` now honors the platform-injected `$PORT` (defaults to 8000 locally).
- `app/db.py` accepts both `postgres://` and `postgresql://` database URLs.

## Path A — Render Blueprint (recommended, ~15 min, free)

1. **Push to GitHub.** From the unzipped project folder on your machine:
   ```bash
   git init
   git add .
   git commit -m "Resume Analyzer v1 — FastAPI + Postgres + JWT"
   ```
   Create an empty repo named `resume-analyzer` on github.com (no README —
   you already have one), then:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<you>/resume-analyzer.git
   git push -u origin main
   ```
   Watch the **CI** tab — the test suite runs automatically on push.

2. **Deploy.** Go to [render.com](https://render.com) → sign up with GitHub →
   **New → Blueprint** → connect the `resume-analyzer` repo → **Apply**.
   `render.yaml` creates the web service + Postgres, wires `DATABASE_URL`,
   and generates a real `JWT_SECRET_KEY` for you. Nothing to paste.

3. **Open it.** After the first build (~5–10 min), visit
   `https://resume-analyzer.onrender.com/app` — register a user, upload a
   PDF resume, save a JD, and run a match. API docs live at `/docs`.

## Path B — manual (any host: Render / Railway / Fly)

If you'd rather click through manually, the only env vars the app needs are:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Your Postgres URL (`postgresql://…`). `postgres://` also works now. |
| `JWT_SECRET_KEY` | A long random string — generate with `openssl rand -hex 32` |
| `OPENAI_API_KEY` | Optional. Leave empty; the built-in analyzer works without it. |

Set the health check to `/health`. Start command is the Docker default.

## Free-tier realities (checked Oct 10, 2026)

- **Sleep:** free web services spin down after ~15 min idle; the first
  request after that takes ~30 s. Normal for a portfolio project.
- **Database expiry:** Render's free Postgres **expires after 90 days**
  (you'll get email warnings). Before expiry, export your data and recreate
  the database — or upgrade. If you want a free Postgres that doesn't
  expire, use [Neon](https://neon.tech) instead and paste its
  `postgresql://` URL as `DATABASE_URL` (skip the Blueprint database).

## After you're live

- Add the live URL + a screenshot to the README (recruiters click these).
- Add the project to LinkedIn Featured and your resume with the live link.
- Every `git push` to `main` redeploys automatically — keep shipping.

## Troubleshooting

- **Build fails** → Render dashboard → your service → **Logs** tab. Usually
  a dependency line in `requirements.txt`.
- **500 on first request** → check `DATABASE_URL` is set and the database
  shows "Available" in the dashboard.
- **Tables missing** → they create on startup; a failed first boot (bad DB
  URL) means a redeploy after fixing the URL.
