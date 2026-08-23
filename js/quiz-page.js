// Wiring for quiz.html. Reads ?set=ch01-s01 (repeatable) from the URL, builds a
// run, then walks setup -> runner -> results.

import { loadManifest, flattenSections } from "./data.js";
import { buildRun, isCorrect, recordAttempt } from "./quiz.js";

const $ = (sel) => document.querySelector(sel);

let rows = [];      // manifest rows for the requested sets
let queue = [];     // questions in this run
let index = 0;
let chosen = new Set();
let answered = false;
const results = [];

init();

async function init() {
  const wanted = new URLSearchParams(location.search).getAll("set");

  let manifest;
  try {
    manifest = await loadManifest();
  } catch (e) {
    fail(e.message);
    return;
  }

  const all = flattenSections(manifest);
  rows = wanted.length ? all.filter((s) => wanted.includes(s.setId)) : all;
  rows = rows.filter((s) => s.status === "generated");

  if (!rows.length) {
    fail("No generated question sets to quiz on. Generate one first, then set its status in data/manifest.json.");
    return;
  }

  $("#quiz-title").textContent = rows.length === 1 ? rows[0].sectionTitle : "Mixed quiz";
  $("#quiz-sub").textContent =
    rows.length === 1
      ? `${rows[0].chapterTitle} · section ${rows[0].sectionNumber}`
      : `${rows.length} sections`;

  $("#setup").hidden = false;
  $("#start").addEventListener("click", start);
  $("#again").addEventListener("click", () => location.reload());
  $("#submit").addEventListener("click", submit);
  $("#next").addEventListener("click", next);
}

async function start() {
  const limit = Number($("#count").value);
  const mode = $("#mode").value;

  try {
    queue = await buildRun(rows.map((r) => r.file), { limit, mode });
  } catch (e) {
    fail(e.message);
    return;
  }

  if (!queue.length) {
    notice(
      mode === "missed"
        ? "Nothing to review — you have not missed any questions in these sections yet."
        : "No questions match that pool."
    );
    return;
  }

  $("#notice").hidden = true;
  $("#setup").hidden = true;
  $("#runner").hidden = false;
  render();
}

function render() {
  const q = queue[index];
  answered = false;
  chosen = new Set();

  $("#quiz-count").textContent = `${index + 1} / ${queue.length}`;
  $("#quiz-fill").style.width = `${(index / queue.length) * 100}%`;

  $("#q-topic").textContent = q.topic ?? "";
  $("#q-stem").textContent = q.stem;

  const multi = q.type === "multi";
  $("#q-choices").innerHTML = q.choices
    .map(
      (c) => `
      <li>
        <button class="choice" data-id="${c.id}" role="checkbox" aria-checked="false">
          <span class="choice-key">${c.id}</span>
          <span class="choice-text">${escape(c.text)}</span>
        </button>
      </li>`
    )
    .join("");

  $("#q-choices")
    .querySelectorAll(".choice")
    .forEach((btn) => btn.addEventListener("click", () => pick(btn, multi)));

  $("#feedback").hidden = true;
  $("#submit").hidden = false;
  $("#submit").disabled = true;
  $("#next").hidden = true;
}

function pick(btn, multi) {
  if (answered) return;
  const id = btn.dataset.id;

  if (multi) {
    if (chosen.has(id)) chosen.delete(id);
    else chosen.add(id);
  } else {
    chosen = new Set([id]);
  }

  $("#q-choices")
    .querySelectorAll(".choice")
    .forEach((b) => {
      const on = chosen.has(b.dataset.id);
      b.classList.toggle("is-picked", on);
      b.setAttribute("aria-checked", String(on));
    });

  $("#submit").disabled = chosen.size === 0;
}

function submit() {
  if (answered || !chosen.size) return;
  answered = true;

  const q = queue[index];
  const correct = isCorrect(q, [...chosen]);
  results.push({ q, chosen: [...chosen], correct });

  // Mark every choice: right answers green, your wrong pick red.
  $("#q-choices")
    .querySelectorAll(".choice")
    .forEach((b) => {
      const id = b.dataset.id;
      b.disabled = true;
      if (q.answer.includes(id)) b.classList.add("is-right");
      else if (chosen.has(id)) b.classList.add("is-wrong");
    });

  $("#fb-verdict").textContent = correct ? "Correct" : "Not quite";
  $("#fb-verdict").className = `fb-verdict ${correct ? "is-right" : "is-wrong"}`;
  $("#fb-explain").textContent = q.explanation ?? "";

  // The whyWrong text is the part that actually teaches something, so show all
  // of it — but when you got it wrong, lead with the option you picked.
  const why = q.whyWrong ?? {};
  const ids = Object.keys(why).sort((a, b) => chosen.has(b) - chosen.has(a));
  $("#fb-why").innerHTML = ids
    .map((id) => {
      const text = q.choices.find((c) => c.id === id)?.text ?? id;
      const mine = chosen.has(id) ? " class=\"is-yours\"" : "";
      return `<li${mine}><strong>${id}.</strong> ${escape(text)} — ${escape(why[id])}</li>`;
    })
    .join("");

  $("#feedback").hidden = false;
  $("#submit").hidden = true;
  $("#next").hidden = false;
  $("#next").textContent = index + 1 >= queue.length ? "See results" : "Next";
  $("#next").focus();
}

function next() {
  index++;
  if (index >= queue.length) finish();
  else render();
}

function finish() {
  const setIds = [...new Set(queue.map((q) => q.setId))];
  const summary = recordAttempt(results, setIds, $("#mode").value);

  $("#runner").hidden = true;
  $("#results").hidden = false;

  const pct = Math.round((summary.score / summary.total) * 100);
  $("#score-line").textContent = `${summary.score} of ${summary.total} correct — ${pct}%`;

  $("#breakdown").innerHTML =
    table("By topic", summary.byTopic) + table("By level", summary.byBloom);
}

function table(title, data) {
  const rows = Object.entries(data)
    .sort((a, b) => a[1].right / a[1].total - b[1].right / b[1].total)
    .map(([k, v]) => {
      const pct = Math.round((v.right / v.total) * 100);
      const band = pct >= 85 ? "good" : pct >= 60 ? "ok" : "bad";
      return `
        <tr>
          <td>${escape(k)}</td>
          <td class="num">${v.right}/${v.total}</td>
          <td class="num" data-band="${band}">${pct}%</td>
        </tr>`;
    })
    .join("");

  if (!rows) return "";
  return `
    <h3 class="card-title">${title}</h3>
    <table class="breakdown"><tbody>${rows}</tbody></table>`;
}

function notice(msg) {
  const el = $("#notice");
  el.textContent = msg;
  el.hidden = false;
}

function fail(msg) {
  $("#quiz-title").textContent = "Could not load";
  const el = $("#notice");
  el.className = "notice is-error";
  el.textContent = msg;
  el.hidden = false;
}

function escape(s) {
  return String(s).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}
