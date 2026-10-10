"""AI tools: bullet rewriter + cover letter generator."""

import app.routers.resumes as resumes_router
from app.services.cover_letter import _extract_name, generate_cover_letter
from app.services.rewriter import _improve_line, rewrite_bullets
from tests.conftest import SAMPLE_RESUME_TEXT

SAMPLE_JD = """Hiring: Backend Engineer (Python).

We need strong Python, REST APIs, Docker and Kubernetes experience.
Familiarity with machine learning is a plus.
"""


def test_improve_line_strips_filler():
    out = _improve_line("responsible for maintaining the API")
    assert out[0].isupper()
    assert "responsible for" not in out.lower()
    assert out.split()[0] in (
        "Built", "Implemented", "Designed", "Analyzed", "Deployed",
        "Collaborated", "Led", "Delivered",
    )


def test_rewrite_bullets_targets_missing_keywords():
    rewrites = rewrite_bullets(SAMPLE_RESUME_TEXT, ["kubernetes", "machine learning"])
    by_kw = [r for r in rewrites if r["original"] is None]
    assert any("kubernetes" in r["suggestion"].lower() for r in by_kw)
    assert any("machine learning" in r["suggestion"].lower() for r in by_kw)
    assert all(r["reason"] for r in rewrites)


def test_extract_name():
    assert _extract_name(SAMPLE_RESUME_TEXT) == "Zennera Maheen"


def test_cover_letter_template_contains_name_and_role():
    letter = generate_cover_letter(
        SAMPLE_RESUME_TEXT, SAMPLE_JD, "Backend Engineer", "Acme", ["python", "docker"]
    )
    assert "Zennera Maheen" in letter
    assert "Backend Engineer" in letter
    assert "Acme" in letter


def _upload(client, auth_headers):
    resumes_router.extract_text_from_pdf = lambda data: SAMPLE_RESUME_TEXT
    files = {"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")}
    return client.post("/resumes/upload", files=files, headers=auth_headers).json()["id"]


def _make_jd(client, auth_headers):
    return client.post(
        "/jds",
        json={"title": "Backend Engineer", "content_text": SAMPLE_JD},
        headers=auth_headers,
    ).json()["id"]


def test_rewrite_endpoint(client, auth_headers):
    resume_id = _upload(client, auth_headers)
    jd_id = _make_jd(client, auth_headers)
    resp = client.post(
        f"/resumes/{resume_id}/rewrite",
        json={"job_description_id": jd_id},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["rewrites"]) > 0
    assert all("suggestion" in r and "reason" in r for r in body["rewrites"])


def test_rewrite_without_jd(client, auth_headers):
    resume_id = _upload(client, auth_headers)
    resp = client.post(
        f"/resumes/{resume_id}/rewrite", json={}, headers=auth_headers
    )
    assert resp.status_code == 201


def test_cover_letter_endpoint(client, auth_headers):
    resume_id = _upload(client, auth_headers)
    jd_id = _make_jd(client, auth_headers)
    resp = client.post(
        f"/resumes/{resume_id}/cover-letter",
        json={"job_description_id": jd_id, "company_name": "Acme Corp"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "Acme Corp" in body["letter_text"]
    assert "Backend Engineer" in body["letter_text"]


def test_cover_letter_requires_jd(client, auth_headers):
    resume_id = _upload(client, auth_headers)
    resp = client.post(
        f"/resumes/{resume_id}/cover-letter",
        json={"job_description_id": 999999},
        headers=auth_headers,
    )
    assert resp.status_code == 404
