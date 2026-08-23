// The quiz runner: pick questions, answer them one at a time, see a score
// broken down by topic and bloom level.
//
// Deliberately one question per screen with feedback shown immediately after
// answering. The whyWrong text is the reason the question sets are expensive to
// generate, so it would be a waste to only show a number at the end.

import { loadSet } from "./data.js";
import { read, write } from "./storage.js";

const LETTERS = ["a", "b", "c", "d", "e"];

/**
 * Build a run from one or more sets.
 * @param {string[]} files   paths relative to data/, from the manifest
 * @param {object} opts
 * @param {number} [opts.limit]     max questions (0 = all)
 * @param {string} [opts.mode]      "all" | "missed" | "unseen"
 * @param {boolean} [opts.shuffle]  shuffle question order (default true)
 */
export async function buildRun(files, opts = {}) {
  const { limit = 0, mode = "all", shuffle = true } = opts;
  const state = read();

  const sets = await Promise.all(files.map((f) => loadSet(f)));
  let pool = [];
  for (const set of sets) {
    for (const q of set.questions ?? []) {
      pool.push({ ...q, setId: set.id, sectionTitle: set.sectionTitle });
    }
  }

  if (mode === "missed") {
    pool = pool.filter((q) => {
      const rec = state.questions[`${q.setId}:${q.id}`];
      return rec && rec.seen > 0 && rec.box === 0;
    });
  } else if (mode === "unseen") {
    pool = pool.filter((q) => !state.questions[`${q.setId}:${q.id}`]?.seen);
  }

  if (shuffle) pool = shuffled(pool);
  if (limit > 0) pool = pool.slice(0, limit);
  return pool;
}

/** Fisher-Yates. */
function shuffled(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** True when the chosen ids match the answer key exactly. */
export function isCorrect(q, chosen) {
  const key = [...(q.answer ?? [])].sort();
  const got = [...chosen].sort();
  return key.length === got.length && key.every((id, i) => id === got[i]);
}

/**
 * Record a run and update per-question Leitner boxes.
 * @param {Array} results  [{ q, chosen, correct }]
 */
export function recordAttempt(results, setIds, mode) {
  const state = read();
  const now = Date.now();
  const byTopic = {};
  const byBloom = {};

  for (const { q, correct } of results) {
    const key = `${q.setId}:${q.id}`;
    const rec = state.questions[key] ?? { seen: 0, wrong: 0, box: 0, lastSeen: null };
    rec.seen++;
    rec.lastSeen = now;
    if (correct) {
      rec.box = Math.min(4, rec.box + 1);
    } else {
      rec.wrong++;
      rec.box = 0;
    }
    state.questions[key] = rec;

    bump(byTopic, q.topic, correct);
    bump(byBloom, q.bloom, correct);
  }

  const score = results.filter((r) => r.correct).length;
  state.attempts.push({
    setIds,
    mode,
    score,
    total: results.length,
    takenAt: now,
    byTopic,
    byBloom,
  });

  write(state);
  return { score, total: results.length, byTopic, byBloom };
}

function bump(acc, key, correct) {
  if (!key) return;
  acc[key] = acc[key] ?? { right: 0, total: 0 };
  acc[key].total++;
  if (correct) acc[key].right++;
}

export { LETTERS };
