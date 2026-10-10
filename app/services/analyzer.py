"""ATS-style resume analysis.

Runs a deterministic heuristic scorer offline. When OPENAI_API_KEY is set, the
result is enriched with one LLM call for role-specific feedback.
"""

import re

import httpx

from app.config import settings

SECTIONS = ["experience", "education", "skills", "projects"]
ACTION_VERBS = [
    "built", "developed", "designed", "led", "implemented", "launched",
    "optimized", "automated", "shipped", "created", "improved", "deployed",
    "architected", "mentored",
]
# Common software-engineering keywords; extend per target role.
ROLE_KEYWORDS = {
    "software engineer": ["python", "javascript", "git", "api", "sql", "testing", "docker"],
    "data scientist": ["python", "sql", "pandas", "machine learning", "statistics", "visualization"],
    "frontend developer": ["javascript", "react", "html", "css", "typescript", "responsive"],
}


def _checklist_score(text: str, target_role: str) -> tuple[int, list[str], dict]:
    lower = text.lower()
    suggestions: list[str] = []
    score = 0
    details: dict = {}

    # 1. Standard sections (40 pts)
    found = [s for s in SECTIONS if s in lower]
    score += round(40 * len(found) / len(SECTIONS))
    details["sections_found"] = found
    for missing in [s for s in SECTIONS if s not in found]:
        suggestions.append(f"Add a '{missing.capitalize()}' section — recruiters scan for it.")

    # 2. Contact info (15 pts)
    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text))
    has_phone = bool(re.search(r"\+?\d[\d\s\-()]{7,}\d", text))
    if has_email:
        score += 8
    else:
        suggestions.append("Add a professional email address at the top.")
    if has_phone:
        score += 7
    else:
        suggestions.append("Add a phone number so recruiters can reach you.")

    # 3. Action verbs (15 pts)
    verbs = [v for v in ACTION_VERBS if v in lower]
    score += min(15, len(verbs) * 3)
    details["action_verbs"] = verbs
    if len(verbs) < 3:
        suggestions.append("Start bullet points with strong action verbs (built, shipped, optimized…).")

    # 4. Length sanity (10 pts)
    words = len(text.split())
    details["word_count"] = words
    if 250 <= words <= 900:
        score += 10
    else:
        suggestions.append("Aim for a focused 1-page resume (roughly 300–700 words).")

    # 5. Role keywords (20 pts)
    keywords = ROLE_KEYWORDS.get(target_role.lower(), ROLE_KEYWORDS["software engineer"])
    hits = [k for k in keywords if k in lower]
    score += round(20 * len(hits) / len(keywords))
    details["keyword_hits"] = hits
    if len(hits) < len(keywords) // 2:
        suggestions.append(
            f"Mirror more '{target_role}' keywords from job descriptions: "
            + ", ".join(k for k in keywords if k not in hits)
        )

    return min(100, score), suggestions, details


def _llm_enrich(text: str, target_role: str, base: dict) -> dict:
    """Optional: ask an LLM for role-specific feedback. Best-effort only."""
    if not settings.openai_api_key:
        return base
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an ATS resume coach. Reply with 3-5 short, specific bullet suggestions.",
                    },
                    {
                        "role": "user",
                        "content": f"Target role: {target_role}\n\nResume text:\n{text[:4000]}",
                    },
                ],
                "max_tokens": 300,
            },
            timeout=20,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        extra = [line.strip("-• ").strip() for line in content.splitlines() if line.strip()]
        base["suggestions"] = base["suggestions"] + [s for s in extra if s][:5]
        base["summary"] += " AI-enriched feedback included."
    except Exception:
        # Never fail an analysis because the LLM call failed.
        pass
    return base


def analyze_resume_text(text: str, target_role: str = "software engineer") -> dict:
    score, suggestions, details = _checklist_score(text, target_role)
    if score >= 80:
        band = "strong"
    elif score >= 55:
        band = "decent but improvable"
    else:
        band = "needs work"
    result = {
        "score": score,
        "summary": (
            f"ATS-style score {score}/100 for '{target_role}' — {band}. "
            f"Checked {len(details.get('sections_found', []))}/{len(SECTIONS)} standard sections, "
            f"{details.get('word_count', 0)} words, "
            f"{len(details.get('keyword_hits', []))} role keywords matched."
        ),
        "suggestions": suggestions,
    }
    return _llm_enrich(text, target_role, result)
