/**
 * Seeds a demo recruiter account with a job + resumes against the running stack,
 * then captures screenshots of the key views into docs/screenshots/.
 *
 * Usage (stack must be up via `docker compose up`):
 *   npx playwright install chromium   # one-time
 *   node docs/capture_screenshots.mjs
 *
 * Env overrides: API_BASE (default http://localhost:8000/api),
 *                APP_BASE (default http://localhost:5173)
 */
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdirSync } from "node:fs";

const API_BASE = process.env.API_BASE ?? "http://localhost:8000/api";
const APP_BASE = process.env.APP_BASE ?? "http://localhost:5173";
const OUT_DIR =
  process.env.SHOTS_DIR ?? join(dirname(fileURLToPath(import.meta.url)), "screenshots");

const SAMPLE_RESUMES = [
  {
    name: "ada_lovelace.txt",
    text: `Ada Lovelace
ada.lovelace@example.com | +1 415 555 0101 | San Francisco, CA
Senior Software Engineer

EXPERIENCE
Senior Software Engineer at Analytical Engines Inc
- Built scalable Python and FastAPI microservices on AWS
- Led a team using React, TypeScript and PostgreSQL
8 years experience

SKILLS
Python, FastAPI, React, TypeScript, PostgreSQL, Docker, AWS, Kubernetes

EDUCATION
Master of Science in Computer Science`,
  },
  {
    name: "alan_turing.txt",
    text: `Alan Turing
alan.turing@example.com | +44 20 7946 0958 | London, UK
Machine Learning Engineer

EXPERIENCE
ML Engineer at Bletchley Systems
- Developed NLP pipelines with Python and PyTorch
- Deployed models with Docker and Redis
6 years experience

SKILLS
Python, PyTorch, NLP, Docker, Redis, SQL

EDUCATION
PhD in Mathematics`,
  },
  {
    name: "grace_hopper.txt",
    text: `Grace Hopper
grace.hopper@example.com | +1 212 555 0173 | New York, NY
Backend Developer

EXPERIENCE
Backend Developer at Cobol Solutions
- Java and Spring services, some Python tooling
4 years experience

SKILLS
Java, Spring, SQL, Python

EDUCATION
Bachelor of Science in Computer Science`,
  },
];

async function api(path, options = {}, token) {
  const headers = { ...(options.headers ?? {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.json) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(options.json);
    delete options.json;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    throw new Error(`${options.method ?? "GET"} ${path} -> ${res.status}: ${await res.text()}`);
  }
  return res.status === 204 ? null : res.json();
}

async function seed() {
  const email = `demo.recruiter+${Date.now()}@screenai.dev`;
  const password = "DemoPass123!";
  const reg = await api("/auth/register", {
    method: "POST",
    json: { email, full_name: "Demo Recruiter", password },
  });
  const token = reg.access_token;
  console.log("Registered demo account:", email);

  const job = await api(
    "/jobs",
    {
      method: "POST",
      json: {
        title: "Senior Backend Engineer",
        department: "Engineering",
        location: "Remote",
        experience: "5+ years",
        min_experience_years: 5,
        salary: "$140k - $180k",
        employment_type: "full_time",
        description:
          "<p>We are looking for a <b>Senior Backend Engineer</b> to build scalable services powering our AI platform.</p>",
        responsibilities:
          "<ul><li>Design and build APIs with Python &amp; FastAPI</li><li>Own data models in PostgreSQL</li><li>Mentor engineers</li></ul>",
        qualifications:
          "<ul><li>5+ years backend experience</li><li>Strong Python, SQL, Docker</li><li>Cloud (AWS) experience</li></ul>",
        skills: ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "React"],
      },
    },
    token,
  );
  console.log("Created job:", job.id);

  const form = new FormData();
  for (const r of SAMPLE_RESUMES) {
    form.append("files", new Blob([r.text], { type: "text/plain" }), r.name);
  }
  await fetch(`${API_BASE}/jobs/${job.id}/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  }).then(async (res) => {
    if (!res.ok) throw new Error(`upload -> ${res.status}: ${await res.text()}`);
  });
  console.log("Uploaded resumes, waiting for scoring...");

  for (let i = 0; i < 40; i++) {
    const prog = await api(`/jobs/${job.id}/progress`, {}, token);
    if (prog.scored + prog.failed >= prog.total && prog.total > 0) break;
    await new Promise((r) => setTimeout(r, 2000));
  }
  console.log("Scoring complete.");
  return { token, jobId: job.id };
}

async function capture({ token, jobId }) {
  mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // Prime auth tokens in localStorage so the SPA boots authenticated.
  await page.goto(APP_BASE);
  await page.evaluate(
    ([access]) => {
      localStorage.setItem("ats_access_token", access);
    },
    [token],
  );

  const shots = [
    { path: "/", file: "dashboard.png" },
    { path: "/jobs", file: "jobs.png" },
    { path: `/jobs/${jobId}/candidates`, file: "candidates.png" },
    { path: `/jobs/${jobId}/upload`, file: "upload.png" },
    { path: "/analytics", file: "analytics.png" },
  ];

  for (const s of shots) {
    await page.goto(`${APP_BASE}${s.path}`, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
    await page.screenshot({ path: join(OUT_DIR, s.file), fullPage: true });
    console.log("Captured", s.file);
  }

  // Candidate detail: click the first candidate row.
  await page.goto(`${APP_BASE}/jobs/${jobId}/candidates`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  const firstRow = page.locator("tbody tr").first();
  if (await firstRow.count()) {
    await firstRow.click();
    await page.waitForTimeout(2500);
    await page.screenshot({ path: join(OUT_DIR, "candidate-detail.png"), fullPage: true });
    console.log("Captured candidate-detail.png");
  }

  await browser.close();
}

const seeded = await seed();
await capture(seeded);
console.log("Done. Screenshots in", OUT_DIR);
