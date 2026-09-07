# Question generation prompt

Attach the section PDF, fill in the bracketed fields, and paste everything below
the line.

Two kinds of set, differing only in `[COUNT]` and scope:

| Kind | `[COUNT]` | Scope | Output |
| --- | --- | --- | --- |
| **Section set** | 20 | One section | `data/<chapterId>/<sectionId>.json` |
| **Chapter review** | 50 | The whole chapter | `data/<chapterId>/review.json` |

Fill in from `data/manifest.json` and `prompts/profiles.json`:

- `[COUNT]` — 20 for a section, 50 for a chapter review
- `[SET ID]` — e.g. `ch03-s02`, or `ch03-review`
- `[CHAPTER N / TITLE]`, `[SECTION N / TITLE]`
- `[PROFILE KEY]` and `[PROFILE GUIDANCE]` — copy the `guidance` string
- `[MIX]` — copy the `mix` object

The profile is **fixed by the chapter's content domain** (Table 5 of the
Orientation chapter — see `text/Orientation.md`). Do not pick one by taste.

**For a chapter review**, attach the whole chapter and set `section` to `0` with
`sectionTitle` "Chapter review". Spread the 50 questions across every section
roughly in proportion to its length, and include 3-5 **blended** items that
require combining two sections — these are the ones a section-by-section study
pass will not have prepared you for.

---

You are writing EPPP practice questions from the attached section PDF.

Produce **[COUNT] multiple-choice questions** as a single JSON object matching
`prompts/schema.json` exactly. Output JSON only — no prose, no code fence.

**Set metadata:** id `[SET ID]`, chapter `[CHAPTER N]` "[CHAPTER TITLE]",
section `[SECTION N]` "[SECTION TITLE]", profile `[PROFILE KEY]`,
sourceFile the attached filename, generatedAt today's date.

**Style profile — `[PROFILE KEY]`:**
[PROFILE GUIDANCE]

**Target level mix (within ~15% of the set size per level):**
[MIX]

## Writing like the real exam

The EPPP has **two** cognitive levels. Every question is one or the other, and
`level` records which.

- **recall** — retrieve stored information: a definition, the assumptions of a
  theory, a research result, the content of a standard.
- **application** — use that information to judge a concrete situation: what
  should this psychologist do, what is this client's most likely diagnosis,
  which technique is being demonstrated.

The distinction is about the *task*, not the length of the stem. Asking "which
of the following defines confabulation?" about a long vignette is still recall.

**Application items are the ones that make a set feel like the exam.** They give
a named practitioner or client, a specific situation, and enough detail to
decide — then ask for the judgment. Model:

> Dr. Kennedy is a skilled cognitive-behavioral psychologist. While attending a
> conference, she stops to talk with a vendor selling biofeedback equipment. The
> vendor, also a therapist, tells Dr. Kennedy his equipment is intuitive to use,
> and that she can easily set it up and apply biofeedback with clients this
> coming week. Dr. Kennedy decides to buy the equipment to try the technique
> with some of her more challenging clients. Dr. Kennedy is _______.

Rather than asking for the *definition* of a concept, an application item gives
an *example* of it and asks what it is. A student who memorized the definition
but does not understand the concept should get it wrong.

### Stem variety

Most stems are either short (a sentence or fragment, usually recall) or a
vignette (several sentences describing a situation). Across the set, also include
a few of these, and set `stemType` accordingly:

- **negative** (2-4 per set) — "all of the following are true except", "which is
  least likely". Never more than this; they are a minority on the real exam.
- **recontextualized** (2-3 per set) — put the concept in an unexpected setting
  so it is not obvious which principle is being tested.
- **blended** (0-2 per set) — require a fact from this section *plus* one from
  another domain. Rare on the exam; do not force these.
- **irrelevant-info** (1-2 per set) — include a detail in the stem that is not
  needed to answer, without making the item ambiguous.

### Distractors

This is where generated sets usually fail. On the real exam, wrong options are
mostly **true statements that do not answer the question asked** — not false
statements.

- Prefer distractors that are accurate about a *neighbouring* concept: a
  different stage, an adjacent standard, another theory from the same framework.
  In a Piaget item, three distractors were all real Piagetian terms.
- Some items should turn on reading the stem precisely, where an option is
  correct about the topic in general but not about what was asked.
- Two or more options should share relevant vocabulary with the correct answer.
  A student who recognizes only the topic word must not be able to pick it out.
- For a "best answer" item, more than one option may be defensible; the
  `explanation` must say why the keyed one is best, and each `whyWrong` must say
  what makes its option weaker — not merely that it is wrong.

## Rules

**Grounding**
- Ground every question in the attached PDF. If it is not in the source, do not
  ask it. No outside knowledge, no "commonly known" facts from elsewhere.
- Application items may invent a *scenario*, but the principle being applied
  must come from the source. Set `sourceRef` to the section/page it comes from.

**Choices**
- Exactly 4 choices per question — always four, never three or five. `type` is
  `single` unless the material genuinely calls for multi-select; keep multi
  under 10% of the set.
- No "all of the above", "none of the above", or "both A and B".
- Do **not** make the correct answer systematically the longest, most detailed,
  or most hedged option. Vary choice length independently of correctness.
- Distribute the answer key roughly evenly across a/b/c/d. No letter should be
  correct more than 35% of the time.

**Coverage**
- No two questions may test the same fact, even reworded.
- Cover the whole section, not just its first few pages.
- `topic`: a 3-6 word concept label. **Reuse labels across questions** so
  results can be grouped. Aim for roughly one topic per 4 questions — about
  5 topics in a 20-question section set, 8-12 in a 50-question chapter
  review — with at least 3 questions each. This is what makes the score
  report useful, so choose the labels deliberately before you start writing.

**Feedback fields**

Match the real exam's rationale structure: it explains the correct answer, then
addresses each wrong option individually.

- `explanation`: 1-3 sentences on *why* the answer is correct — the underlying
  rule or mechanism, citing the standard or concept by name where the source
  does. Never a restatement of the correct choice's text.
- `whyWrong`: one entry per incorrect choice, naming the *specific* misconception
  that would lead a student to pick it. "This is wrong" is not acceptable. Good:
  "Even though biofeedback is related to behavioral techniques, its use requires
  specific training." Where an option is true but not responsive, say so — that
  it is accurate but misses the issue the question turns on.

**Process**
- First, list the topic labels you will use and how many questions each gets,
  and the recall/application split you are aiming for. Then generate the
  questions in batches of about 15 so quality does not degrade in the tail.
  Continue until you have [COUNT], then emit the final JSON.
- Before emitting, self-check: [COUNT] questions, unique sequential ids, exactly
  4 choices each, every `answer` id present in that question's `choices`, a
  `whyWrong` entry for every non-answer choice, answer-key spread under 35% per
  letter, and the recall/application counts within ±5 of the target mix.

After writing the file, run `python tools/validate.py data/<ch>/<s>.json` (or
`node tools/validate.mjs`) and fix anything it reports.
