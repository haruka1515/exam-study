# Reading a scanned section into notes

The chapter PDFs are scans, so a section starts as page images in
`text/<name>.sNN/`. This is the step that turns them into `text/<name>.sNN.md`,
which `generate.md` then reads.

## What these notes are

**Condensed study notes in your own words — not a transcript.** The chapter is
copyrighted course material. Paraphrase the substance; quote only short phrases
where the exact wording is itself the thing being tested ("substantial harm",
"reasonable steps", "the emergency has ended"). Keep standard numbers and
citations so anything can be looked up in the source.

`text/` is gitignored for this reason. The questions derived from these notes are
your own work and are committed; the notes are not.

## Write for question generation, not for reading

This is the part that matters, and it is counterintuitive: **the shortest notes
so far produced the best questions.**

| Section | Note words | Words per question | Rework needed |
| --- | --- | --- | --- |
| s03 Resolving Ethical Issues | 585 | 19 | least |
| s04 Competence | 782 | 26 | least |
| s01 Introduction | 1,750 | 87 | more |
| s02 The Ethics Code | 4,093 | 204 | most |

s03 and s04 are not shorter because they leave things out. They are shorter
because they are **decision-shaped** — organized around what a question can test
rather than around the chapter's headings. Notes that merely mirror the source's
structure force the testable structure to be re-derived while writing questions,
and that is where question quality goes.

Capture, for each provision:

- **The rule** — what is required, permitted, or prohibited.
- **The trigger** — the condition under which it applies. This becomes the
  scenario in a vignette.
- **The exception or overriding limit** — the "but not when…" clause. These are
  disproportionately testable; one such line in s03 (confidentiality outranks the
  duty to report) generated five questions.
- **The contrast** — the neighbouring provision it gets confused with. This is
  where good distractors come from.

## Four shapes worth using

**A contrast table** wherever provisions form a graded response or a parallel
set. Each row is a question: give a scenario matching one trigger and make the
other row's action a distractor.

| | When it applies | What to do |
| --- | --- | --- |
| **1.04 Informal** | Informal resolution "appears appropriate" | Discuss with the offending psychologist |
| **1.05 Formal** | "Substantial harm" and unsuited to informal resolution, **or** informal resolution failed | Report to the Ethics Committee, licensing board, or other authority |

**Exceptions called out on their own line**, in bold. Do not bury them in a
paragraph — they are the highest-yield sentences in the section.

**Worked examples, kept whole.** The book's examples are there because they are
testable. Record the situation and its resolution; changing the names gives you
an exam-shaped vignette almost directly.

**Exhaustive enumerations, marked as exhaustive.** "Three examples: sexual
misconduct, insurance fraud, plagiarism" is a recall item where the distractors
are real-but-unlisted violations. Note when a list is complete, because that is
what makes it safe to test.

Also keep, verbatim in structure:

- **Research citations** — author, year, and the finding. Ladany et al. (1999)
  and Simon's (1992) two factors each became questions directly.
- **Terms of art** — the exam tests these as definitions.
- **Numbers** — thresholds, counts, time limits.
- **Programmed review items** at the end of a section. They are the book's own
  statement of what it considers testable; treat them as a checklist that the
  notes cover everything they touch.

## Layout

Start each file with the header the existing sections use:

```markdown
# Ethics — 5. Standard 3: Human Relations

Section 5 of `Ethics.pdf`, printed pages 83-86.
Page images: `Ethics.s05/`

**Condensed study notes, not a transcript.** Short quoted phrases are terms of
art the exam tests directly. See the page images for exact wording.

**Key concepts:** …the section's own Key Concepts list, if it has one
```

Then one `##` per lettered subsection, following the source's own divisions so a
question's `sourceRef` can point at something real.

## Then

Generate with `prompts/generate.md` at `[COUNT]` 20, and polish with
`tools/polish.py` — which enforces expanding distractors *before* rebalancing the
answer key, an ordering that is silent and destructive to get wrong.
