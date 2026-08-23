# Report questions whose correct answer is the longest choice.
#
#   python tools/delength.py data/ch01/s02.json
#   python tools/delength.py --list data/ch01/s02.json
#
# The validator warns when the correct answer is the longest option too often,
# because that lets a student score without reading the stem. This locates the
# offending questions and prints the choice text, so the distractors can be
# rewritten to match — by hand, or by feeding the output to a model.
#
# It deliberately does NOT edit anything. Padding distractors mechanically
# produces limp, obviously-filler options, which is a different way of making a
# question guessable. The rewrite has to be written, not generated.

import argparse
import json
import pathlib
import sys


def offenders(questions):
    out = []
    for q in questions:
        if q.get("type") != "single" or len(q.get("answer") or []) != 1:
            continue
        lengths = {c["id"]: len(c["text"]) for c in q["choices"]}
        ans = q["answer"][0]
        longest = max(lengths.values())
        if lengths[ans] == longest and list(lengths.values()).count(longest) == 1:
            runner_up = max(v for k, v in lengths.items() if k != ans)
            out.append((lengths[ans] - runner_up, q))
    out.sort(key=lambda t: -t[0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--list", action="store_true", help="print the full choice text of each")
    ap.add_argument("--top", type=int, default=0, help="only show the N worst")
    args = ap.parse_args()

    for name in args.files:
        path = pathlib.Path(name)
        data = json.loads(path.read_text(encoding="utf-8"))
        qs = data.get("questions") or []
        bad = offenders(qs)
        singles = sum(1 for q in qs if q.get("type") == "single")
        share = len(bad) / singles if singles else 0

        print(f"{path.as_posix()}: answer is longest in {len(bad)}/{singles} ({share:.0%})")
        rows = bad[: args.top] if args.top else bad
        for margin, q in rows:
            print(f"\n  {q['id']}  (+{margin} chars over the next longest)")
            if args.list:
                print(f"    stem: {q['stem']}")
                for c in q["choices"]:
                    mark = "*" if c["id"] in q["answer"] else " "
                    print(f"    {mark}{c['id']}. [{len(c['text']):3d}] {c['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
