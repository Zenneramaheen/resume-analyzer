"""Resume <-> Job Description matching.

Deterministic keyword-overlap matcher: extracts the important terms from a
job description and reports which ones appear in the resume.
"""

import re
from collections import Counter

STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "our", "are", "will",
    "have", "has", "had", "this", "that", "from", "into", "they", "them",
    "their", "there", "what", "when", "where", "which", "who", "whom",
    "about", "above", "after", "again", "all", "also", "any", "because",
    "been", "before", "being", "between", "both", "but", "can", "did",
    "each", "few", "her", "here", "him", "how", "its", "more", "most",
    "not", "only", "other", "over", "same", "should", "such", "than",
    "too", "very", "was", "were", "while", "who", "work", "working",
    "role", "team", "join", "looking", "seeking", "candidate", "ideal",
    "plus", "including", "within", "across", "able", "etc",
}

# Multi-word terms worth detecting as a unit.
COMPOUND_TERMS = [
    "machine learning", "data science", "deep learning",
    "natural language processing", "artificial intelligence",
    "software engineer", "data analyst", "web development",
    "rest api", "ci/cd", "large language model",
]


def extract_keywords(text: str, top_n: int = 40) -> list[str]:
    """Return the most important terms in a document, most frequent first."""
    lower = text.lower()
    compounds = [t for t in COMPOUND_TERMS if t in lower]
    words = re.findall(r"[a-z][a-z0-9+#.\-]*", lower)
    tokens = [w.strip(".-") for w in words]
    tokens = [t for t in tokens if len(t) >= 3 and t not in STOPWORDS]
    counts = Counter(tokens)
    ranked = sorted(counts, key=lambda w: (-counts[w], w))
    keywords = compounds + [w for w in ranked if w not in compounds]
    return keywords[:top_n]


def match_resume_to_jd(resume_text: str, jd_text: str) -> dict:
    """Score how well a resume covers a job description's key terms."""
    jd_keywords = extract_keywords(jd_text)
    resume_terms = set(extract_keywords(resume_text, top_n=300))

    matched = [k for k in jd_keywords if k in resume_terms]
    missing = [k for k in jd_keywords if k not in resume_terms]
    score = round(100 * len(matched) / len(jd_keywords)) if jd_keywords else 0

    suggestions = [
        f"The job description mentions '{k}' — add it if you genuinely have that skill or experience."
        for k in missing[:8]
    ]
    if not missing:
        suggestions.append("Excellent coverage — your resume hits every key term in this job description.")

    return {
        "score": score,
        "summary": (
            f"JD match score {score}/100 — {len(matched)} of {len(jd_keywords)} "
            "key terms from the job description found in your resume."
        ),
        "suggestions": suggestions,
        "matched_keywords": matched,
        "missing_keywords": missing,
    }
