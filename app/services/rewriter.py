"""Bullet-point rewriting.

Heuristic pass (offline, deterministic):
  1. Finds weak bullets (not starting with an action verb) and rewrites them.
  2. Drafts tailored starter bullets for keywords missing vs. a job description.

When OPENAI_API_KEY is set, an LLM pass polishes the suggestions (best-effort).
"""

import httpx

from app.config import settings
from app.services.analyzer import ACTION_VERBS

FILLER_STARTS = [
    "responsible for ",
    "worked on ",
    "helped with ",
    "involved in ",
    "tasked with ",
]

VERB_BY_HINT = [
    ("api", "Built"),
    ("test", "Implemented"),
    ("design", "Designed"),
    ("data", "Analyzed"),
    ("deploy", "Deployed"),
    ("team", "Collaborated with"),
    ("led", "Led"),
]


def _improve_line(line: str) -> str:
    """Rewrite a weak bullet to start with a strong action verb."""
    low = line.lower()
    for filler in FILLER_STARTS:
        if low.startswith(filler):
            line = line[len(filler):]
            low = line.lower()
            break
    verb = "Delivered"
    for hint, candidate in VERB_BY_HINT:
        if hint in low:
            verb = candidate
            break
    line = line[0].upper() + line[1:] if line else line
    return f"{verb} {line}"


def _starts_with_verb(line: str) -> bool:
    first = line.split()[0].lower().rstrip(",.") if line.split() else ""
    return first in ACTION_VERBS


def _candidate_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("-•*· ").strip()
        if len(line) >= 25:
            lines.append(line)
    return lines


def _template_for(keyword: str) -> str:
    kw = keyword.lower()
    if kw in {"docker", "kubernetes", "ci/cd", "git", "jenkins", "terraform"}:
        return (
            f"Automated build and deployment workflows with {keyword}, "
            "reducing release time and errors — add your measured impact."
        )
    if kw in {
        "machine learning", "deep learning", "natural language processing",
        "artificial intelligence", "large language model",
    }:
        return (
            f"Built {keyword} solutions for [problem] — "
            "fill in your dataset, model and measured result."
        )
    if kw in {"sql", "postgresql", "mongodb", "redis", "elasticsearch"}:
        return f"Designed and optimized {keyword} data models and queries for [application]."
    if kw in {"react", "typescript", "html", "css", "next.js", "vue"}:
        return f"Developed responsive interfaces with {keyword}, improving experience for [users]."
    if kw in {"testing", "pytest", "jest", "cypress"}:
        return f"Implemented {keyword} suites covering [area], catching regressions pre-release."
    return (
        f"Leveraged {keyword} to [achievement] — "
        "tailor this with your specific project and a metric."
    )


def _llm_polish(resume_text: str, rewrites: list[dict]) -> list[dict]:
    """Best-effort LLM pass. Returns original rewrites on any failure."""
    if not settings.openai_api_key:
        return rewrites
    try:
        prompt = (
            "You are a resume coach. Improve these bullet suggestions for a software "
            "engineering resume. Keep each under 25 words, start with an action verb, "
            "keep the [bracket] placeholders where the writer must add specifics.\n\n"
        )
        for i, r in enumerate(rewrites[:8], 1):
            prompt += f"{i}. {r['suggestion']}\n"
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
            },
            timeout=25,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        polished = [ln.strip("0123456789. )") for ln in content.splitlines() if ln.strip()]
        for r, p in zip(rewrites, polished):
            if p:
                r["suggestion"] = p
    except Exception:
        pass
    return rewrites


def rewrite_bullets(resume_text: str, missing_keywords: list[str] | None = None) -> list[dict]:
    """Return a list of {original, suggestion, reason} rewrite items."""
    missing_keywords = missing_keywords or []
    rewrites: list[dict] = []

    for line in _candidate_lines(resume_text)[:40]:
        if not _starts_with_verb(line):
            rewrites.append(
                {
                    "original": line[:180],
                    "suggestion": _improve_line(line),
                    "reason": "Bullet doesn't start with an action verb — recruiters skim first words.",
                }
            )
            if len(rewrites) >= 5:
                break

    for kw in missing_keywords[:6]:
        rewrites.append(
            {
                "original": None,
                "suggestion": _template_for(kw),
                "reason": f"Your resume doesn't mention '{kw}', which the job description asks for.",
            }
        )

    return _llm_polish(resume_text, rewrites)
