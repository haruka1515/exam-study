# Even out a question set's answer key by permuting each question's choices.
#
#   python tools/rebalance.py data/ch01/s01.json
#
# Writing 50+ questions by hand tends to park the correct answer on the same
# letter, which the validator flags as guessable. The fix is mechanical: the
# choices are a set, not a sequence, so reordering them changes nothing about
# the question. Choice text, the answer, and the whyWrong mapping all move
# together; only the letters change.
#
# Greedy and deterministic: questions are walked in order and each one's answer
# is assigned to whichever letter is least used so far, so reruns are stable and
# the diff is reviewable.

import argparse
import collections
import json
import pathlib
import sys

LETTERS = ["a", "b", "c", "d", "e"]


def rebalance(qs):
    counts = collections.Counter()
    moved = 0

    for q in qs:
        choices = q.get("choices") or []
        answer = q.get("answer") or []
        if len(answer) != 1 or q.get("type") != "single":
            # Multi-answer questions have no single key letter to balance.
            for a in answer:
                counts[a] += 1
            continue

        letters = [c["id"] for c in choices]
        by_id = {c["id"]: c["text"] for c in choices}
        why = dict(q.get("whyWrong") or {})
        old_answer = answer[0]

        # Least-used letter available in this question wins the answer slot.
        target = min(letters, key=lambda L: (counts[L], LETTERS.index(L)))

        # slot letter -> which of the old choice ids now sits in that slot. The
        # answer takes the target slot; the rest fill the others in order.
        source = {}
        remaining = [L for L in letters if L != old_answer]
        for slot in letters:
            if slot == target:
                source[slot] = old_answer
            else:
                source[slot] = remaining.pop(0)

        q["choices"] = [{"id": slot, "text": by_id[source[slot]]} for slot in letters]
        q["answer"] = [target]
        q["whyWrong"] = {
            slot: why[source[slot]] for slot in letters if slot != target and source[slot] in why
        }

        counts[target] += 1
        if target != old_answer:
            moved += 1

    return counts, moved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()

    for name in args.files:
        path = pathlib.Path(name)
        data = json.loads(path.read_text(encoding="utf-8"))
        counts, moved = rebalance(data.get("questions") or [])
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        total = sum(counts.values())
        spread = "  ".join(f"{L}={counts[L]} ({counts[L]/total:.0%})" for L in LETTERS if counts[L])
        print(f"{path.as_posix()}: {moved} question(s) re-lettered -> {spread}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
