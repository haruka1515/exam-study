// Shared validation logic for question sets.
//
// Pure — no filesystem, no DOM — so it runs identically in three places:
//   * the browser (validate.html, and a warning badge in the app)
//   * GitHub Actions on every push (tools/validate.mjs)
//   * anywhere else you have a JS runtime
//
// Errors are contract violations that would break the quiz or teach you
// something false. Warnings are quality smells worth a look.

export const BLOOMS = ["recall", "understand", "apply", "analyze"];
const BANNED = ["all of the above", "none of the above", "both a and b", "a and b only"];

/**
 * @param {object} set        parsed question-set JSON
 * @param {object} [opts]
 * @param {object} [opts.profiles]  contents of prompts/profiles.json
 * @param {number} [opts.expected]  expected question count (default 50)
 * @returns {{errors: string[], warnings: string[]}}
 */
export function validateSet(set, opts = {}) {
  const profiles = opts.profiles ?? {};
  const expected = opts.expected ?? 50;
  const errors = [];
  const warnings = [];
  const err = (m) => errors.push(m);
  const warn = (m) => warnings.push(m);

  if (!set || typeof set !== "object") {
    err("not a JSON object");
    return { errors, warnings };
  }

  for (const field of ["id", "chapter", "section", "profile", "questions"]) {
    if (set[field] === undefined) err(`missing top-level field "${field}"`);
  }
  if (!Array.isArray(set.questions)) {
    err('"questions" must be an array');
    return { errors, warnings };
  }

  if (typeof set.id === "string") {
    const m = /^ch(\d{2})-s(\d{2})$/.exec(set.id);
    if (!m) err(`id "${set.id}" should look like "ch03-s02"`);
    else {
      if (Number(m[1]) !== set.chapter) err(`id "${set.id}" disagrees with chapter ${set.chapter}`);
      if (Number(m[2]) !== set.section) err(`id "${set.id}" disagrees with section ${set.section}`);
    }
  }
  if (set.profile && Object.keys(profiles).length && !profiles[set.profile]) {
    warn(`profile "${set.profile}" is not defined in prompts/profiles.json`);
  }

  const qs = set.questions;
  if (qs.length !== expected) warn(`${qs.length} questions (expected ${expected})`);

  const seenIds = new Set();
  const seenStems = new Map();
  const keyCount = { a: 0, b: 0, c: 0, d: 0, e: 0 };
  const bloomCount = Object.fromEntries(BLOOMS.map((b) => [b, 0]));
  const topics = new Map();
  let singles = 0;
  let longestIsAnswer = 0;

  qs.forEach((q, i) => {
    const at = `q[${i}]${q && q.id ? ` (${q.id})` : ""}`;
    if (!q || typeof q !== "object") {
      err(`${at}: not an object`);
      return;
    }

    if (!q.id) err(`${at}: missing id`);
    else if (seenIds.has(q.id)) err(`${at}: duplicate question id "${q.id}"`);
    else seenIds.add(q.id);

    if (!["single", "multi"].includes(q.type)) err(`${at}: type must be "single" or "multi"`);

    if (typeof q.stem !== "string" || q.stem.trim().length < 10) {
      err(`${at}: stem missing or too short`);
    } else {
      const norm = q.stem.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
      if (seenStems.has(norm)) err(`${at}: stem duplicates ${seenStems.get(norm)}`);
      else seenStems.set(norm, q.id ?? at);
    }

    if (!Array.isArray(q.choices) || q.choices.length < 4) {
      err(`${at}: needs at least 4 choices`);
      return;
    }
    const choiceIds = q.choices.map((c) => c && c.id);
    if (new Set(choiceIds).size !== choiceIds.length) err(`${at}: duplicate choice ids`);
    const texts = q.choices.map((c) => String((c && c.text) ?? "").trim().toLowerCase());
    if (texts.some((t) => !t)) err(`${at}: a choice has empty text`);
    if (new Set(texts).size !== texts.length) err(`${at}: two choices have identical text`);
    for (const t of texts) {
      if (BANNED.some((b) => t.includes(b))) warn(`${at}: banned choice pattern ("${t}")`);
    }

    if (!Array.isArray(q.answer) || q.answer.length === 0) {
      err(`${at}: answer must be a non-empty array of choice ids`);
      return;
    }
    for (const a of q.answer) {
      if (!choiceIds.includes(a)) err(`${at}: answer "${a}" is not one of its choices`);
    }
    if (q.type === "single" && q.answer.length !== 1) {
      err(`${at}: type "single" but ${q.answer.length} correct answers`);
    }
    if (q.type === "multi" && q.answer.length < 2) {
      err(`${at}: type "multi" but only 1 correct answer`);
    }

    const ww = q.whyWrong ?? {};
    for (const c of choiceIds.filter((c) => !q.answer.includes(c))) {
      if (!ww[c] || String(ww[c]).trim().length < 10) {
        err(`${at}: whyWrong missing or too short for choice "${c}"`);
      }
    }
    for (const c of Object.keys(ww)) {
      if (q.answer.includes(c)) warn(`${at}: whyWrong has an entry for correct choice "${c}"`);
    }

    if (typeof q.explanation !== "string" || q.explanation.trim().length < 20) {
      err(`${at}: explanation missing or too short`);
    }
    if (typeof q.topic !== "string" || q.topic.trim().length < 3) {
      err(`${at}: missing topic label`);
    } else {
      const t = q.topic.trim();
      topics.set(t, (topics.get(t) ?? 0) + 1);
    }
    if (!BLOOMS.includes(q.bloom)) err(`${at}: bloom must be one of ${BLOOMS.join(", ")}`);
    else bloomCount[q.bloom]++;
    if (!Number.isInteger(q.difficulty) || q.difficulty < 1 || q.difficulty > 3) {
      err(`${at}: difficulty must be an integer 1-3`);
    }

    // Guessability checks — only meaningful for single-answer questions.
    if (q.type === "single" && q.answer.length === 1) {
      singles++;
      keyCount[q.answer[0]] = (keyCount[q.answer[0]] ?? 0) + 1;
      const lengths = q.choices.map((c) => String((c && c.text) ?? "").length);
      const max = Math.max(...lengths);
      const answerIdx = choiceIds.indexOf(q.answer[0]);
      if (lengths[answerIdx] === max && lengths.filter((l) => l === max).length === 1) {
        longestIsAnswer++;
      }
    }
  });

  if (singles >= 10) {
    for (const [letter, n] of Object.entries(keyCount)) {
      if (n / singles > 0.35) {
        warn(`answer key skewed: "${letter}" is correct ${n}/${singles} times (${pct(n / singles)})`);
      }
    }
    if (longestIsAnswer / singles > 0.45) {
      warn(
        `length cue: the longest choice is correct ${longestIsAnswer}/${singles} times ` +
          `(${pct(longestIsAnswer / singles)}) — guessable without reading the stem`
      );
    }
  }

  if (topics.size && qs.length >= 20) {
    if (topics.size < 6) warn(`only ${topics.size} distinct topics — results breakdown will be coarse`);
    if (topics.size > 15) warn(`${topics.size} distinct topics — too fragmented to group results by`);
    const singletons = [...topics].filter(([, n]) => n === 1).map(([t]) => t);
    if (singletons.length > 3) {
      warn(`${singletons.length} topics have only one question (e.g. "${singletons[0]}")`);
    }
  }

  const mix = profiles[set.profile] && profiles[set.profile].mix;
  if (mix && qs.length) {
    for (const b of BLOOMS) {
      const want = ((mix[b] ?? 0) / 100) * qs.length;
      const got = bloomCount[b];
      if (Math.abs(got - want) > Math.max(5, qs.length * 0.15)) {
        warn(`bloom "${b}": ${got} questions, profile "${set.profile}" targets ~${Math.round(want)}`);
      }
    }
  }

  return { errors, warnings };
}

function pct(x) {
  return `${Math.round(x * 100)}%`;
}
