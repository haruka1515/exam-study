// Per-device study record, kept in localStorage.
//
// Shape:
//   {
//     version: 1,
//     attempts: [ { setIds, mode, score, total, takenAt, byTopic, byBloom } ],
//     questions: { "ch03-s02:q07": { seen, wrong, lastSeen, box } }
//   }
//
// `questions` powers the "previously missed" filter and the Leitner box used
// for spaced repetition. `box` is 0-4; right answers promote, wrong resets to 0.

const KEY = "exam-study:v1";

const EMPTY = { version: 1, attempts: [], questions: {} };

export function read() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return structuredClone(EMPTY);
    const parsed = JSON.parse(raw);
    return { ...structuredClone(EMPTY), ...parsed };
  } catch {
    // Private mode, cleared storage, or corrupt data — start clean rather than break.
    return structuredClone(EMPTY);
  }
}

export function write(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
    return true;
  } catch {
    return false;
  }
}

/** Most recent attempt that covered this section, or null. */
export function lastAttemptFor(setId, state = read()) {
  for (let i = state.attempts.length - 1; i >= 0; i--) {
    const a = state.attempts[i];
    if (a.setIds?.includes(setId)) return a;
  }
  return null;
}

/** Summary used by the home grid: last score as a fraction, and how many are still wrong. */
export function sectionSummary(setId, state = read()) {
  const last = lastAttemptFor(setId, state);
  let missed = 0;
  const prefix = setId + ":";
  for (const [k, v] of Object.entries(state.questions)) {
    if (k.startsWith(prefix) && v.box === 0 && v.seen > 0) missed++;
  }
  return {
    attempted: Boolean(last),
    ratio: last && last.total ? last.score / last.total : null,
    takenAt: last?.takenAt ?? null,
    missed,
  };
}

export function exportJson(state = read()) {
  return JSON.stringify(state, null, 2);
}

export function importJson(text) {
  const parsed = JSON.parse(text);
  if (!parsed || typeof parsed !== "object" || !Array.isArray(parsed.attempts)) {
    throw new Error("That file does not look like an exam-study export.");
  }
  write(parsed);
  return parsed;
}
