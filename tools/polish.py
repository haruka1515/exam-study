"""Run the guessability fixes on a question set, in the order that is safe.

Two cues let you score a set without knowing the material, and both are easy to
introduce while writing questions:

  * a skewed answer key   — fixed by re-lettering choices (tools/rebalance.py)
  * a length cue          — the correct answer is the longest option

The order matters, and getting it wrong is silent. rebalance.py re-letters the
choices, so any edit addressed by LETTER after a rebalance lands on a different
choice than intended — which overwrites correct answers with distractor text
while leaving the file structurally valid. The validator cannot catch that.

So: expand distractors first, rebalance second, and address edits by TEXT.
This script enforces that ordering and refuses to modify a keyed answer.

Usage
  python tools/polish.py --report data/ch02/s05.json      # what needs fixing
  python tools/polish.py --edits edits.json data/...json  # apply, then rebalance

The edits file is {"original choice text": "expanded replacement", ...}.
Expand DISTRACTORS with real content — never trim the correct answer, and never
pad with filler, which just makes the question guessable a different way.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

CHANCE = 0.25  # four choices, so a length cue only matters above this


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def longest_offenders(qs):
    """Questions where the keyed answer is the single longest choice."""
    out = []
    for q in qs:
        if q.get("type") != "single" or len(q.get("answer", [])) != 1:
            continue
        lengths = {c["id"]: len(c["text"]) for c in q["choices"]}
        keyed = q["answer"][0]
        others = [v for k, v in lengths.items() if k != keyed]
        if others and lengths[keyed] > max(others):
            out.append((q["id"], lengths[keyed] - max(others)))
    return sorted(out, key=lambda t: -t[1])


def report(path):
    data = load(path)
    qs = data["questions"]
    n = len(qs)

    keys = {}
    for q in qs:
        if len(q.get("answer", [])) == 1:
            keys[q["answer"][0]] = keys.get(q["answer"][0], 0) + 1
    levels = {}
    for q in qs:
        levels[q.get("level")] = levels.get(q.get("level"), 0) + 1

    print(f"{path}: {n} questions")
    print("  level    ", "  ".join(f"{k}={v}" for k, v in sorted(levels.items())))
    print("  key      ", "  ".join(f"{k}={v}" for k, v in sorted(keys.items())))

    offenders = longest_offenders(qs)
    pct = len(offenders) / n if n else 0
    flag = "" if pct <= CHANCE else "   <-- above chance, fix this"
    print(f"  longest-is-answer  {len(offenders)}/{n} ({pct:.0%}){flag}")
    for qid, margin in offenders[:12]:
        print(f"      {qid}  +{margin} chars over the next longest")
    if len(offenders) > 12:
        print(f"      ... and {len(offenders) - 12} more")
    return offenders


def apply_edits(path, edits_path):
    data = load(path)
    edits = load(edits_path)

    # Resolve every edit before writing anything: a refusal must leave the file
    # untouched rather than half-applied.
    pending = []
    refused = 0
    unmatched = set(edits)
    for q in data["questions"]:
        for c in q["choices"]:
            new = edits.get(c["text"])
            if new is None:
                continue
            unmatched.discard(c["text"])
            if c["id"] in q["answer"]:
                print(f"  REFUSED (keyed answer) {q['id']} choice {c['id']}")
                refused += 1
            else:
                pending.append((c, new))

    for miss in sorted(unmatched):
        print(f"  NO MATCH: {miss[:70]}")

    if refused:
        print(f"{path}: unchanged — {refused} edit(s) target a keyed answer")
        return refused

    for choice, new in pending:
        choice["text"] = new
    save(path, data)
    print(f"{path}: {len(pending)} distractors expanded")
    return 0


def rebalance(path):
    """Re-letter choices to even the answer key. Always last."""
    tool = Path(__file__).with_name("rebalance.py")
    return subprocess.run([sys.executable, str(tool), path], check=False).returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--report", action="store_true", help="show the cues, change nothing")
    ap.add_argument("--edits", help="JSON map of original choice text -> replacement")
    ap.add_argument("--no-rebalance", action="store_true", help="skip the rebalance step")
    args = ap.parse_args()

    if args.report or not args.edits:
        report(args.file)
        if not args.edits:
            return

    print()
    if apply_edits(args.file, args.edits):
        sys.exit("refused to edit a keyed answer — fix the edits file and retry")

    if not args.no_rebalance:
        print()
        rebalance(args.file)

    print()
    report(args.file)


if __name__ == "__main__":
    main()
