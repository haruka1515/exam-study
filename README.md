# exam-study

A static exam-prep quiz player. Question sets are generated offline from section
PDFs and committed as JSON; the site just reads them.

```
PDF  ──►  [Claude, offline]  ──►  data/chNN/sMM.json  ──►  [static site]
          ~70 times, once           the contract          used daily
```

**Why the split.** Generation is slow, expensive, and needs review — a wrong
answer key you don't catch teaches you something false. Keeping it offline gives
you a review step for free, and keeps the site a fast, dependency-free thing that
loads instantly on a phone. The two halves only ever agree on one thing: the
question-set JSON schema.

## Layout

| Path | What it is |
| --- | --- |
| `index.html` | The dashboard: progress, and a chip per section. |
| `quiz.html`, `js/quiz*.js` | The quiz player — one question per screen, feedback as you go, score by topic and bloom level. |
| `css/`, `js/` | Plain CSS and ES modules — no build step, no dependencies. |
| `data/manifest.json` | Every chapter and section: titles, question-style profile, file path, status. Edit this first. |
| `data/chNN/sMM.json` | One generated question set per section. |
| `prompts/generate.md` | The generation prompt. Paste with a PDF attached. |
| `prompts/profiles.json` | Question-style profiles (knowledge-heavy, scenario-heavy, …) and their bloom mixes. |
| `prompts/schema.json` | JSON Schema for a question set — the contract. |
| `js/validate-core.js` | The quality checks, shared by the browser and CI. |
| `tools/validate.mjs` | CLI wrapper for the same checks (needs Node). |
| `tools/validate.py` | The same checks in Python, for when Node isn't installed. |
| `tools/extract.py` | PDF → text, or → page images when the PDF is a scan. |
| `tools/rebalance.py` | Evens out a skewed answer key by re-lettering choices. |
| `tools/delength.py` | Finds questions where the correct answer is the longest choice. |
| `pdfs/` | Your source PDFs. **Gitignored** — see below. |
| `text/` | Extracted text and page images. **Gitignored** — same content, same copyright. |

## Setup, once

1. Fill in `data/manifest.json`: course name, exam date, and the real chapter and
   section titles. Set each chapter's `profile` to the question style that
   chapter needs (see `prompts/profiles.json`).
2. Push to GitHub, then **Settings → Pages → Deploy from branch → `main` / root**.
   The site is live in about 30 seconds.

## The loop, per section

1. Drop the section PDF in `pdfs/`, then run `python tools/extract.py`.
   It works out whether the PDF has a real text layer or is a scan, and writes
   `text/<name>.md` either way. Scanned pages also land as PNGs for Claude to
   read directly — see below.
2. Open a Claude session, attach the PDF (or point it at `text/`), and paste
   `prompts/generate.md` with the four bracketed fields filled in from
   `manifest.json` and `profiles.json`.
3. Save the JSON to `data/chNN/sMM.json`, and flip that section's `status` to
   `"generated"` in `manifest.json`.
4. Validate — `python tools/validate.py`, or `npm run validate` with Node, or
   open `validate.html` in the browser. Fix anything red. Skim a few by eye.
5. `git commit && git push`. Study.

### Scanned PDFs

Printed-from-the-web textbook chapters are usually images with nothing but a
watermark in the text layer, so extraction returns almost nothing.
`tools/extract.py` detects this by measuring words per page, and renders each
page to `text/<name>.pages/pNNN.png` instead. Claude reads those images
directly — there is no OCR step and nothing to install for it. Transcribe them
into `text/<name>.md` once, and the chapter is reusable as text from then on.

### Two quality checks worth knowing

Writing 50+ questions in one pass reliably produces two biases the validator
catches, both of which let you score without knowing the material:

- **A skewed answer key** — `python tools/rebalance.py data/chNN/sMM.json`
  re-letters the choices to even it out. Choices are a set, so reordering
  changes nothing about the question.
- **A length cue**, where the correct answer is the longest option.
  `python tools/delength.py --list data/chNN/sMM.json` prints the offenders.
  Fix these by expanding the *distractors* with real content — padding them
  with filler just makes the question guessable a different way.

## Validation

The checks catch the failure modes that quietly ruin a study session: an answer
id that isn't one of the choices, a duplicated question, a missing `whyWrong`, an
answer key that's 60% "c", or a set where the longest choice is correct often
enough to guess from. They run in three places, from the same module:

- **In the browser** — `validate.html`, no install needed.
- **In CI** — GitHub Actions runs them on every push that touches `data/`.
- **On the CLI** — `node tools/validate.mjs`, if you install Node.

## Two things to know

**Don't commit the PDFs.** They're copyrighted course material and a Pages repo is
public by default. `pdfs/` is gitignored. The generated questions are your own
derived work and are fine to commit.

**Progress is per-device.** Attempt history and per-question stats live in
`localStorage`, so your laptop and your phone keep separate records. Use the
export/import buttons to move progress between them.
