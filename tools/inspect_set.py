"""Inspect a question set: the mix, the guessability cues, and structural health.

This exists because generating a section repeatedly needs the same few answers —
is the recall/application split right for the profile, is the answer key even, is
the correct answer systematically the longest, are the topics usable for a score
breakdown — and running ad-hoc Python for each one is both slow and a permission
prompt every time.

Usage
  python tools/inspect_set.py data/ch02/s09.json           # summary
  python tools/inspect_set.py data/ch02/s09.json --show q07 q12   # print items
  python tools/inspect_set.py data/ch02/*.json             # several at once
"""

import argparse
import json
from collections import Counter

CHANCE = 0.25          # four choices
CUE_MARGIN = 8         # chars; below this a length difference is no real cue


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def length_offenders(qs):
    """(id, margin) where the keyed answer is the single longest choice."""
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


def structural_problems(qs):
    problems = []
    for q in qs:
        ids = {c["id"] for c in q["choices"]}
        texts = [c["text"].strip().lower() for c in q["choices"]]
        if len(set(texts)) != len(texts):
            problems.append(f"{q['id']}: two choices have identical text")
        if len(q["choices"]) != 4:
            problems.append(f"{q['id']}: {len(q['choices'])} choices, expected 4")
        if not set(q["answer"]) <= ids:
            problems.append(f"{q['id']}: answer id not among its choices")
        expected = ids - set(q["answer"])
        if set(q.get("whyWrong", {})) != expected:
            problems.append(f"{q['id']}: whyWrong keys do not match the wrong choices")
    return problems


def report(path, profiles):
    data = load(path)
    qs = data["questions"]
    n = len(qs)
    profile = data.get("profile")

    levels = Counter(q.get("level") for q in qs)
    keys = Counter(q["answer"][0] for q in qs if len(q.get("answer", [])) == 1)
    topics = Counter(q.get("topic") for q in qs)
    stems = Counter(q.get("stemType") for q in qs)

    print(f"\n{path}   {n} questions   profile: {profile}")

    mix = (profiles.get(profile) or {}).get("mix") or {}
    parts = []
    for level, count in sorted(levels.items()):
        if mix:
            want = round(mix.get(level, 0) / 100 * n)
            flag = "" if abs(count - want) <= max(2, n * 0.15) else "  <-- off target"
            parts.append(f"{level}={count} (target ~{want}){flag}")
        else:
            parts.append(f"{level}={count}")
    print("  level      " + "   ".join(parts))

    spread = "  ".join(f"{k}={v}" for k, v in sorted(keys.items()))
    worst = max(keys.values()) / n if keys else 0
    print(f"  key        {spread}" + ("   <-- skewed" if worst > 0.35 else ""))

    offenders = length_offenders(qs)
    real = [o for o in offenders if o[1] >= CUE_MARGIN]
    pct = len(offenders) / n if n else 0
    line = f"  length cue {len(offenders)}/{n} ({pct:.0%})"
    if real:
        line += f"   {len(real)} with a margin >= {CUE_MARGIN} chars  <-- fix these"
    elif offenders:
        line += f"   all margins < {CUE_MARGIN} chars, no practical cue"
    print(line)
    for qid, margin in real[:8]:
        print(f"       {qid}  +{margin}")

    print(f"  topics     {len(topics)}: " + ", ".join(f"{t} ({c})" for t, c in topics.most_common()))
    if stems:
        print("  stems      " + "  ".join(f"{k}={v}" for k, v in stems.most_common() if k))

    problems = structural_problems(qs)
    for p in problems:
        print(f"  PROBLEM    {p}")
    return problems


def show(path, ids):
    data = load(path)
    for q in data["questions"]:
        if ids and q["id"] not in ids:
            continue
        keyed = q["answer"]
        print(f"\n=== {q['id']}  [{q.get('level')}/{q.get('stemType')}]  {q.get('topic')}")
        print(f"    {q['stem']}")
        for c in q["choices"]:
            mark = "*" if c["id"] in keyed else " "
            print(f"  {mark} {c['id']} [{len(c['text']):3d}] {c['text']}")
        print(f"    WHY: {q.get('explanation','')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--show", nargs="*", metavar="QID", help="print full items (all, or the ids given)")
    args = ap.parse_args()

    try:
        with open("prompts/profiles.json", encoding="utf-8") as fh:
            profiles = json.load(fh)
    except OSError:
        profiles = {}

    if args.show is not None:
        for path in args.files:
            show(path, set(args.show))
        return

    any_problem = False
    for path in args.files:
        if report(path, profiles):
            any_problem = True
    print()
    if any_problem:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
