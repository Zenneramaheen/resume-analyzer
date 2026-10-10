// Same-origin when served from FastAPI (/app); override for split dev setups.
const API_BASE = "";

const $ = (id) => document.getElementById(id);
let mode = "login";

function setMode(next) {
  mode = next;
  $("tab-login").classList.toggle("active", next === "login");
  $("tab-register").classList.toggle("active", next === "register");
  $("auth-submit").textContent = next === "login" ? "Log in" : "Register";
}
$("tab-login").onclick = () => setMode("login");
$("tab-register").onclick = () => setMode("register");

const token = () => localStorage.getItem("token");
const authHeaders = () => ({ Authorization: `Bearer ${token()}` });

function showApp(show) {
  $("auth-view").classList.toggle("hidden", show);
  $("app-view").classList.toggle("hidden", !show);
  $("logout-btn").classList.toggle("hidden", !show);
  if (show) {
    loadResumes();
    loadJds();
  }
}

$("auth-form").onsubmit = async (e) => {
  e.preventDefault();
  $("auth-error").textContent = "";
  const body = { email: $("email").value, password: $("password").value };
  try {
    if (mode === "register") {
      const r = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error((await r.json()).detail || "Registration failed");
    }
    const r = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: body.email, password: body.password }),
    });
    if (!r.ok) throw new Error("Invalid email or password");
    localStorage.setItem("token", (await r.json()).access_token);
    showApp(true);
  } catch (err) {
    $("auth-error").textContent = err.message;
  }
};

$("logout-btn").onclick = () => {
  localStorage.removeItem("token");
  showApp(false);
};

$("upload-form").onsubmit = async (e) => {
  e.preventDefault();
  $("upload-error").textContent = "";
  const file = $("pdf-file").files[0];
  if (!file) return;
  try {
    const form = new FormData();
    form.append("file", file);
    const up = await fetch(`${API_BASE}/resumes/upload`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    });
    if (!up.ok) throw new Error((await up.json()).detail || "Upload failed");
    const resume = await up.json();

    const an = await fetch(`${API_BASE}/resumes/${resume.id}/analyze`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ target_role: $("target-role").value || "software engineer" }),
    });
    if (!an.ok) throw new Error("Analysis failed");
    renderResult(await an.json());
    loadResumes();
  } catch (err) {
    $("upload-error").textContent = err.message;
  }
};

function renderResult(a) {
  $("result-card").classList.remove("hidden");
  $("score-num").textContent = a.score;
  const ring = $("score-ring");
  ring.style.borderColor = a.score >= 80 ? "var(--good)" : a.score >= 55 ? "var(--warn)" : "var(--danger)";
  $("result-summary").textContent = a.summary;
  $("suggestions").innerHTML = a.suggestions.map((s) => `<li>${s}</li>`).join("");
  const hasKw = a.matched_keywords || a.missing_keywords;
  $("keywords").classList.toggle("hidden", !hasKw);
  if (hasKw) {
    $("matched-kw").innerHTML = (a.matched_keywords || []).map((k) => `<span>${k}</span>`).join("");
    $("missing-kw").innerHTML = (a.missing_keywords || []).map((k) => `<span>${k}</span>`).join("");
  }
  $("result-card").scrollIntoView({ behavior: "smooth" });
}

async function loadResumes() {
  const r = await fetch(`${API_BASE}/resumes`, { headers: authHeaders() });
  if (!r.ok) return;
  const resumes = await r.json();
  $("resume-list").innerHTML = resumes.length
    ? resumes
        .map(
          (x) =>
            `<li><span>${x.filename}</span><button data-id="${x.id}">Re-analyze</button></li>`
        )
        .join("")
    : "<li>No resumes yet.</li>";
  document.querySelectorAll("#resume-list button").forEach((b) => {
    b.onclick = async () => {
      const an = await fetch(`${API_BASE}/resumes/${b.dataset.id}/analyze`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ target_role: $("target-role").value || "software engineer" }),
      });
      if (an.ok) renderResult(await an.json());
    };
  });
  refreshMatchResumes();
}

if (token()) showApp(true);

// ---- Job descriptions ----
async function loadJds() {
  const r = await fetch(`${API_BASE}/jds`, { headers: authHeaders() });
  if (!r.ok) return;
  const jds = await r.json();
  $("jd-list").innerHTML = jds.length
    ? jds
        .map(
          (j) =>
            `<li><span>${j.title}</span><button data-id="${j.id}">Delete</button></li>`
        )
        .join("")
    : "<li>No job descriptions saved yet.</li>";
  $("match-jd").innerHTML = jds
    .map((j) => `<option value="${j.id}">${j.title}</option>`)
    .join("");
  document.querySelectorAll("#jd-list button").forEach((b) => {
    b.onclick = async () => {
      await fetch(`${API_BASE}/jds/${b.dataset.id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      loadJds();
    };
  });
}

$("jd-form").onsubmit = async (e) => {
  e.preventDefault();
  const r = await fetch(`${API_BASE}/jds`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ title: $("jd-title").value, content_text: $("jd-text").value }),
  });
  if (r.ok) {
    $("jd-title").value = "";
    $("jd-text").value = "";
    loadJds();
  }
};

// ---- Matching ----
async function refreshMatchResumes() {
  const r = await fetch(`${API_BASE}/resumes`, { headers: authHeaders() });
  if (!r.ok) return;
  const resumes = await r.json();
  $("match-resume").innerHTML = resumes
    .map((x) => `<option value="${x.id}">${x.filename}</option>`)
    .join("");
}

$("match-form").onsubmit = async (e) => {
  e.preventDefault();
  $("match-error").textContent = "";
  const resumeId = $("match-resume").value;
  const jdId = $("match-jd").value;
  if (!resumeId || !jdId) {
    $("match-error").textContent = "Upload a resume and save a job description first.";
    return;
  }
  const r = await fetch(`${API_BASE}/resumes/${resumeId}/match`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ job_description_id: Number(jdId) }),
  });
  if (!r.ok) {
    $("match-error").textContent = "Match failed.";
    return;
  }
  renderResult(await r.json());
};

function selectedPair() {
  const resumeId = $("match-resume").value;
  const jdId = $("match-jd").value;
  if (!resumeId || !jdId) {
    $("match-error").textContent = "Upload a resume and save a job description first.";
    return null;
  }
  $("match-error").textContent = "";
  return { resumeId, jdId };
}

function showAiCard(title, html) {
  $("ai-card").classList.remove("hidden");
  $("ai-title").textContent = title;
  $("ai-body").innerHTML = html;
  $("ai-card").scrollIntoView({ behavior: "smooth" });
}

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

$("rewrite-btn").onclick = async () => {
  const pair = selectedPair();
  if (!pair) return;
  const r = await fetch(`${API_BASE}/resumes/${pair.resumeId}/rewrite`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ job_description_id: Number(pair.jdId) }),
  });
  if (!r.ok) {
    $("match-error").textContent = "Rewrite failed.";
    return;
  }
  const data = await r.json();
  showAiCard(
    "Suggested rewrites",
    data.rewrites
      .map(
        (w) => `<div class="rewrite-item">${
          w.original ? `<div class="original">✎ ${esc(w.original)}</div>` : ""
        }<div class="suggestion">→ ${esc(w.suggestion)}</div><div class="reason">${esc(w.reason)}</div></div>`
      )
      .join("") || "<p>No suggestions — your bullets already look strong.</p>"
  );
};

$("letter-btn").onclick = async () => {
  const pair = selectedPair();
  if (!pair) return;
  const r = await fetch(`${API_BASE}/resumes/${pair.resumeId}/cover-letter`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      job_description_id: Number(pair.jdId),
      company_name: $("company-name").value || "",
    }),
  });
  if (!r.ok) {
    $("match-error").textContent = "Cover letter failed.";
    return;
  }
  const data = await r.json();
  showAiCard(
    "Cover letter",
    `<pre id="letter-text">${esc(data.letter_text)}</pre><button id="copy-letter">Copy to clipboard</button>`
  );
  $("copy-letter").onclick = () => navigator.clipboard.writeText(data.letter_text);
};
