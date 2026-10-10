"""Cover letter generation.

Template-based offline; LLM-generated when OPENAI_API_KEY is set.
"""

import httpx

from app.config import settings


def _extract_name(resume_text: str) -> str:
    for line in resume_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "@" in line or "://" in line or len(line.split()) > 5:
            continue
        return line
    return "Applicant"


def _template_letter(name: str, role: str, company: str, matched: list[str]) -> str:
    company = company or "your company"
    skills = ", ".join(matched[:5]) if matched else "relevant technical skills"
    return f"""Dear Hiring Manager,

I am excited to apply for the {role} at {company}. As a software engineer with hands-on experience across the stack, I was drawn to this role because it sits exactly at the intersection of what I do best and what I want to keep learning.

My background includes {skills}. I enjoy owning problems end to end — from designing the approach to shipping and measuring the result — and I am comfortable picking up new tools quickly when the problem demands it.

I would welcome the chance to discuss how I can contribute to your team. Thank you for your consideration.

Sincerely,
{name}"""


def _llm_letter(resume_text: str, jd_text: str, role: str, company: str) -> str | None:
    if not settings.openai_api_key:
        return None
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Write a concise, professional cover letter (under 200 words). "
                            "No placeholders, no invented experience — only use what the resume states."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Role: {role}\nCompany: {company or 'the company'}\n\n"
                            f"Resume:\n{resume_text[:3000]}\n\nJob description:\n{jd_text[:3000]}"
                        ),
                    },
                ],
                "max_tokens": 400,
            },
            timeout=25,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def generate_cover_letter(
    resume_text: str,
    jd_text: str,
    role: str,
    company: str,
    matched_keywords: list[str],
) -> str:
    letter = _llm_letter(resume_text, jd_text, role, company)
    if letter:
        return letter
    return _template_letter(_extract_name(resume_text), role, company, matched_keywords)
