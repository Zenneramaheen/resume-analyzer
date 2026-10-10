"""Job description CRUD + resume<->JD matching."""

import app.routers.resumes as resumes_router
from app.services.matcher import extract_keywords, match_resume_to_jd
from tests.conftest import SAMPLE_RESUME_TEXT

SAMPLE_JD = """We are hiring a Software Engineer (Python).

Requirements:
- Strong Python and JavaScript skills
- Experience with REST APIs, SQL and Docker
- Knowledge of Kubernetes and machine learning is a plus
- Git version control and automated testing
"""


def test_extract_keywords():
    kws = extract_keywords(SAMPLE_JD)
    assert "python" in kws
    assert "machine learning" in kws  # compound term detection
    assert "the" not in kws


def test_match_scores_coverage():
    result = match_resume_to_jd(SAMPLE_RESUME_TEXT, SAMPLE_JD)
    assert 0 <= result["score"] <= 100
    assert "python" in result["matched_keywords"]
    assert "kubernetes" in result["missing_keywords"]
    assert result["suggestions"]


def _upload(client, auth_headers):
    resumes_router.extract_text_from_pdf = lambda data: SAMPLE_RESUME_TEXT
    files = {"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")}
    return client.post("/resumes/upload", files=files, headers=auth_headers)


def _make_jd(client, auth_headers):
    resp = client.post(
        "/jds",
        json={"title": "SWE Python", "content_text": SAMPLE_JD},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


def test_jd_crud(client, auth_headers):
    jd = _make_jd(client, auth_headers)
    assert jd["title"] == "SWE Python"

    listed = client.get("/jds", headers=auth_headers).json()
    assert any(x["id"] == jd["id"] for x in listed)

    assert client.get(f"/jds/{jd['id']}", headers=auth_headers).status_code == 200
    assert client.delete(f"/jds/{jd['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/jds/{jd['id']}", headers=auth_headers).status_code == 404


def test_match_endpoint(client, auth_headers):
    resume_id = _upload(client, auth_headers).json()["id"]
    jd_id = _make_jd(client, auth_headers)["id"]

    resp = client.post(
        f"/resumes/{resume_id}/match",
        json={"job_description_id": jd_id},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert 0 <= body["score"] <= 100
    assert "kubernetes" in body["missing_keywords"]
    assert body["suggestions"]

    # match is stored in analysis history
    history = client.get(f"/resumes/{resume_id}/analyses", headers=auth_headers).json()
    assert any(h["id"] == body["id"] for h in history)


def test_match_unknown_jd_404(client, auth_headers):
    resume_id = _upload(client, auth_headers).json()["id"]
    resp = client.post(
        f"/resumes/{resume_id}/match",
        json={"job_description_id": 999999},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_jds_require_auth(client):
    assert client.get("/jds").status_code == 401
