# Question generation prompt

Attach the section PDF, fill in the four bracketed fields, and paste everything
below the line. Output goes to `data/<chapterId>/<sectionId>.json`.

Fill in from `data/manifest.json` and `prompts/profiles.json`:

- `[SET ID]` — e.g. `ch03-s02`
- `[CHAPTER N / TITLE]`, `[SECTION N / TITLE]`
- `[PROFILE KEY]` and `[PROFILE GUIDANCE]` — copy the `guidance` string
- `[MIX]` — copy the `mix` object

---

You are writing exam questions from the attached section PDF.

Produce **50 multiple-choice questions** as a single JSON object matching
`prompts/schema.json` exactly. Output JSON only — no prose, no code fence.

**Set metadata:** id `[SET ID]`, chapter `[CHAPTER N]` "[CHAPTER TITLE]",
section `[SECTION N]` "[SECTION TITLE]", profile `[PROFILE KEY]`,
sourceFile the attached filename, generatedAt today's date.

**Style profile — `[PROFILE KEY]`:**
[PROFILE GUIDANCE]

**Target bloom mix (approximate, ±5 questions per level):**
[MIX]

## Rules

**Grounding**
- Ground every question in the attached PDF. If it is not in the source, do not
  ask it. No outside knowledge, no "commonly known" facts from elsewhere.
- Set `sourceRef` to the section/page the question comes from.

**Choices**
- Exactly 4 choices per question. `type` is `single` unless the material
  genuinely calls for multi-select; keep multi under 10% of the set.
- Distractors must be plausible to someone who half-learned the material.
  Draw them from adjacent concepts in this same section — never invent
  terminology, never use obviously absurd options as filler.
- No "all of the above", "none of the above", or "both A and B".
- Do **not** make the correct answer systematically the longest, most detailed,
  or most hedged option. Vary choice length independently of correctness.
- Distribute the answer key roughly evenly across a/b/c/d. No letter should be
  correct more than 35% of the time.

**Coverage**
- No two questions may test the same fact, even reworded.
- Cover the whole section, not just its first few pages.
- `topic`: a 3-6 word concept label. **Reuse labels across questions** so
  results can be grouped — aim for 8-12 distinct topics across the 50, with
  3-6 questions each. This is what makes the score report useful, so choose
  the labels deliberately before you start writing questions.

**Feedback fields**
- `explanation`: 1-3 sentences on *why* the answer is correct — the underlying
  rule or mechanism. Never a restatement of the correct choice's text.
- `whyWrong`: one entry per incorrect choice, naming the *specific*
  misconception that would lead a student to pick it. "This is wrong" is not
  acceptable; "this is the behavior of TCP Tahoe, not Reno" is.

**Process**
- First, list the 8-12 topic labels you will use and how many questions each
  gets. Then generate the questions in batches of 15 so quality does not
  degrade in the tail. Continue until you have 50, then emit the final JSON.
- Before emitting, self-check: 50 questions, unique `q` ids (`q01`..`q50`),
  every `answer` id present in that question's `choices`, a `whyWrong` entry
  for every non-answer choice, answer-key spread under 35% per letter.

After writing the file, run `node tools/validate.mjs data/<ch>/<s>.json` and
fix anything it reports.
