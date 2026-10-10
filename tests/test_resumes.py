"""Resume upload + analysis flow (PDF parsing is stubbed for determinism)."""

import app.routers.resumes as resumes_router
from tests.conftest import SAMPLE_RESUME_TEXT


def _upload(client, auth_headers):
    resumes_router.extract_text_from_pdf = lambda data: SAMPLE_RESUME_TEXT
    files = {"file": ("resume.pdf", b"%PDF-1.4 fake-bytes", "application/pdf")}
    return client.post("/resumes/upload", files=files, headers=auth_headers)


def test_upload_pdf(client, auth_headers):
    resp = _upload(client, auth_headers)
    assert resp.status_code == 201
    assert resp.json()["filename"] == "resume.pdf"


def test_upload_rejects_non_pdf(client, auth_headers):
    files = {"file": ("notes.txt", b"hello", "text/plain")}
    resp = client.post("/resumes/upload", files=files, headers=auth_headers)
    assert resp.status_code == 400


def test_analyze_resume(client, auth_headers):
    resume_id = _upload(client, auth_headers).json()["id"]
    resp = client.post(
        f"/resumes/{resume_id}/analyze",
        json={"target_role": "software engineer"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert 0 <= body["score"] <= 100
    assert isinstance(body["suggestions"], list)
    assert body["summary"]


def test_analysis_history(client, auth_headers):
    resume_id = _upload(client, auth_headers).json()["id"]
    client.post(f"/resumes/{resume_id}/analyze", json={}, headers=auth_headers)
    resp = client.get(f"/resumes/{resume_id}/analyses", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_list_resumes_requires_auth(client):
    assert client.get("/resumes").status_code == 401
