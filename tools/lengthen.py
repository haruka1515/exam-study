# Rewrite specific choice texts, matching on a snippet of the current text.
#
#   python tools/lengthen.py data/ch02/s04.json edits.json
#
# Companion to tools/delength.py, which finds the questions where the correct
# answer is the longest choice. That bias is easy to introduce by hand — correct
# answers tend to state a full two-part condition while distractors stay short —
# and it lets a student score without reading the stem.
#
# Editing those choices by hand is unreliable once tools/rebalance.py has
# shuffled the letters, so this matches on a snippet of the text instead of on a
# choice id. Edits survive re-lettering.
#
# edits.json maps question id -> list of [snippet, replacement] pairs:
#   {"q05": [["without restriction", "Providing the services without any ..."]]}
#
# Refuses to touch a choice that is the answer: expanding distractors is the
# cure, trimming the correct answer just moves the problem.

import json
import pathlib
import sys


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: lengthen.py <set.json> <edits.json>")

    set_path = pathlib.Path(sys.argv[1])
    edits = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    data = json.loads(set_path.read_text(encoding="utf-8"))

    by_id = {q["id"]: q for q in data["questions"]}
    applied = misses = 0

    for qid, pairs in edits.items():
        q = by_id.get(qid)
        if q is None:
            print(f"  no such question: {qid}")
            misses += 1
            continue
        for snippet, replacement in pairs:
            hits = [c for c in q["choices"] if snippet.lower() in c["text"].lower()]
            if len(hits) != 1:
                print(f"  {qid}: {len(hits)} matches for {snippet!r} — skipped")
                misses += 1
                continue
            if hits[0]["id"] in q["answer"]:
                print(f"  {qid}: {snippet!r} is the ANSWER — refusing to edit")
                misses += 1
                continue
            hits[0]["text"] = replacement
            applied += 1

    set_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"{set_path.as_posix()}: {applied} choice(s) rewritten, {misses} skipped")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
