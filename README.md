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
| `index.html`, `css/`, `js/` | The quiz player. Plain HTML/CSS/ES modules — no build step, no dependencies. |
| `data/manifest.json` | Every chapter and section: titles, question-style profile, file path, status. Edit this first. |
| `data/chNN/sMM.json` | One generated question set per section. |
| `prompts/generate.md` | The generation prompt. Paste with a PDF attached. |
| `prompts/profiles.json` | Question-style profiles (knowledge-heavy, scenario-heavy, …) and their bloom mixes. |
| `prompts/schema.json` | JSON Schema for a question set — the contract. |
| `js/validate-core.js` | The quality checks, shared by the browser and CI. |
| `tools/validate.mjs` | CLI wrapper for the same checks. |
| `pdfs/` | Your source PDFs. **Gitignored** — see below. |

## Setup, once

1. Fill in `data/manifest.json`: course name, exam date, and the real chapter and
   section titles. Set each chapter's `profile` to the question style that
   chapter needs (see `prompts/profiles.json`).
2. Push to GitHub, then **Settings → Pages → Deploy from branch → `main` / root**.
   The site is live in about 30 seconds.

## The loop, per section

1. Drop the section PDF in `pdfs/`.
2. Open a Claude session, attach the PDF, and paste `prompts/generate.md` with
   the four bracketed fields filled in from `manifest.json` and `profiles.json`.
3. Save the JSON to `data/chNN/sMM.json`, and flip that section's `status` to
   `"generated"` in `manifest.json`.
4. Validate — open `validate.html` in the browser, or `npm run validate` if you
   have Node. Fix anything red. Skim three or four questions by eye.
5. `git commit && git push`. Study.

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
