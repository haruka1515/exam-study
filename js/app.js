// Landing page: overall progress, then a card per chapter with a chip per section.
// The test builder / runner / results screens come next; section chips currently
// open a detail panel and stop there.

import { loadManifest, flattenSections, countPlaceholders, daysUntil } from "./data.js";
import { read, sectionSummary } from "./storage.js";

const $ = (sel) => document.querySelector(sel);

let manifest = null;
let sections = [];
let filter = "all";

init();

async function init() {
  try {
    manifest = await loadManifest();
  } catch (e) {
    fail(e.message);
    return;
  }

  const state = read();
  sections = flattenSections(manifest).map((s) => ({ ...s, ...sectionSummary(s.setId, state) }));

  renderHeader(manifest);
  renderOverview();
  renderChapters();
  wireFilters();
}

// --- header ----------------------------------------------------------------

function renderHeader(manifest) {
  const todos = countPlaceholders(manifest);
  $("#course").textContent = isTodo(manifest.course) ? "Your course" : manifest.course;

  const chapters = manifest.chapters?.length ?? 0;
  $("#subtitle").textContent = `${chapters} chapters · ${sections.length} sections`;

  const days = daysUntil(manifest.exam);
  if (days !== null) {
    $("#countdown").hidden = false;
    $("#countdown-num").textContent = days;
    $("#countdown").classList.toggle("is-urgent", days <= 14);
  }

  if (todos > 0) {
    notice(
      `<strong>${todos} placeholder${todos === 1 ? "" : "s"} in <code>data/manifest.json</code>.</strong> ` +
        `Fill in the course name, exam date, and chapter and section titles — this page renders straight from that file.`
    );
  }
}

// --- overview --------------------------------------------------------------

function renderOverview() {
  const ready = sections.filter((s) => s.status === "generated");
  const attempted = sections.filter((s) => s.attempted);
  const pct = sections.length ? Math.round((ready.length / sections.length) * 100) : 0;

  $("#meter-label").textContent = `${ready.length} of ${sections.length} sections generated`;
  $("#meter-pct").textContent = `${pct}%`;
  $("#bar-fill").style.width = `${pct}%`;

  const avg = attempted.length
    ? Math.round((attempted.reduce((n, s) => n + s.ratio, 0) / attempted.length) * 100) + "%"
    : "—";
  const missed = sections.reduce((n, s) => n + s.missed, 0);

  $("#stats").innerHTML = [
    stat("Sections studied", `${attempted.length}`),
    stat("Average score", avg),
    stat("Questions to revisit", missed ? `${missed}` : "—"),
  ].join("");
}

function stat(label, value) {
  return `<div class="stat"><dt>${label}</dt><dd>${value}</dd></div>`;
}

// --- chapters --------------------------------------------------------------

function renderChapters() {
  const host = $("#chapters");
  const visible = sections.filter(matchesFilter);

  if (!visible.length) {
    host.innerHTML = `<p class="empty">No sections match this filter.</p>`;
    return;
  }

  host.innerHTML = (manifest.chapters ?? [])
    .map((ch) => {
      const rows = sections.filter((s) => s.chapterId === ch.id && matchesFilter(s));
      if (!rows.length) return "";
      const ready = sections.filter((s) => s.chapterId === ch.id && s.status === "generated").length;
      const total = sections.filter((s) => s.chapterId === ch.id).length;

      return `
        <article class="chapter">
          <header class="chapter-head">
            <span class="chapter-num">${ch.number}</span>
            <div class="chapter-titles">
              <h2>${escape(isTodo(ch.title) ? `Chapter ${ch.number}` : ch.title)}</h2>
              <p class="muted">
                <span class="tag">${escape(ch.profile ?? "no profile")}</span>
                ${ready} of ${total} generated
              </p>
            </div>
          </header>
          <ul class="sections">
            ${rows.map(sectionChip).join("")}
          </ul>
        </article>`;
    })
    .join("");

  host.querySelectorAll("[data-set]").forEach((el) => {
    el.addEventListener("click", () => openDetail(el.dataset.set));
  });
}

function sectionChip(s) {
  const state = s.status !== "generated" ? "pending" : s.attempted ? scoreBand(s.ratio) : "ready";
  const label = isTodo(s.sectionTitle) ? `Section ${s.chapterNumber}.${s.sectionNumber}` : s.sectionTitle;
  const score = s.attempted ? `${Math.round(s.ratio * 100)}%` : s.status === "generated" ? "ready" : "—";

  return `
    <li>
      <button class="section" data-set="${s.setId}" data-state="${state}">
        <span class="section-num">${s.sectionNumber}</span>
        <span class="section-title">${escape(label)}</span>
        <span class="section-score">${score}</span>
      </button>
    </li>`;
}

function scoreBand(r) {
  if (r >= 0.85) return "good";
  if (r >= 0.6) return "ok";
  return "bad";
}

function openDetail(setId) {
  const s = sections.find((x) => x.setId === setId);
  if (!s) return;

  if (s.status === "generated") {
    location.href = `quiz.html?set=${encodeURIComponent(setId)}`;
    return;
  }

  notice(
    `<strong>${escape(s.setId)}</strong> — ${escape(s.profile ?? "no profile")} · ` +
      `not generated yet. Run <code>prompts/generate.md</code> against the section PDF.`
  );
}

// --- filters ---------------------------------------------------------------

function matchesFilter(s) {
  if (filter === "ready") return s.status === "generated";
  if (filter === "pending") return s.status !== "generated";
  if (filter === "weak") return s.attempted && s.ratio < 0.7;
  return true;
}

function wireFilters() {
  document.querySelectorAll("[data-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-filter]").forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      filter = btn.dataset.filter;
      renderChapters();
    });
  });
}

// --- helpers ---------------------------------------------------------------

function notice(html) {
  const el = $("#notice");
  el.innerHTML = html;
  el.hidden = false;
}

function fail(msg) {
  $("#course").textContent = "Could not load";
  const el = $("#notice");
  el.className = "notice is-error";
  el.textContent = msg;
  el.hidden = false;
}

function isTodo(s) {
  return typeof s === "string" && s.trim().toUpperCase().startsWith("TODO");
}

function escape(s) {
  return String(s).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}
