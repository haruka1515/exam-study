# Python port of js/validate-core.js, for checking question sets without Node.
#
#   python tools/validate.py                      # every set under data/
#   python tools/validate.py data/ch01/s01.json
#   python tools/validate.py --expect 68 data/ch01/s01.json
#
# js/validate-core.js remains the source of truth — it is what CI and the
# browser run. Keep the two in sync when the rules change.

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOOMS = ["recall", "understand", "apply", "analyze"]
BANNED = ["all of the above", "none of the above", "both a and b", "a and b only"]


def validate_set(s, profiles, expected):
    errors, warnings = [], []
    err, warn = errors.append, warnings.append

    if not isinstance(s, dict):
        return ["not a JSON object"], []

    for field in ("id", "chapter", "section", "profile", "questions"):
        if s.get(field) is None:
            err(f'missing top-level field "{field}"')

    qs = s.get("questions")
    if not isinstance(qs, list):
        err('"questions" must be an array')
        return errors, warnings

    sid = s.get("id")
    if isinstance(sid, str):
        import re

        m = re.match(r"^ch(\d{2})-s(\d{2})$", sid)
        if not m:
            err(f'id "{sid}" should look like "ch03-s02"')
        else:
            if int(m.group(1)) != s.get("chapter"):
                err(f'id "{sid}" disagrees with chapter {s.get("chapter")}')
            if int(m.group(2)) != s.get("section"):
                err(f'id "{sid}" disagrees with section {s.get("section")}')

    if s.get("profile") and profiles and s["profile"] not in profiles:
        warn(f'profile "{s["profile"]}" is not defined in prompts/profiles.json')

    # A set may declare its own target; short sections cannot support as many
    # distinct questions as long ones. Mirrors js/validate-core.js.
    target = s.get("questionTarget")
    if not isinstance(target, int) or isinstance(target, bool):
        target = expected
    if len(qs) != target:
        warn(f"{len(qs)} questions (expected {target})")

    seen_ids, seen_stems = set(), {}
    key_count = {k: 0 for k in "abcde"}
    bloom_count = {b: 0 for b in BLOOMS}
    topics = {}
    singles = 0
    longest_is_answer = 0

    for i, q in enumerate(qs):
        at = f"q[{i}]" + (f" ({q['id']})" if isinstance(q, dict) and q.get("id") else "")
        if not isinstance(q, dict):
            err(f"{at}: not an object")
            continue

        qid = q.get("id")
        if not qid:
            err(f"{at}: missing id")
        elif qid in seen_ids:
            err(f'{at}: duplicate question id "{qid}"')
        else:
            seen_ids.add(qid)

        if q.get("type") not in ("single", "multi"):
            err(f'{at}: type must be "single" or "multi"')

        stem = q.get("stem")
        if not isinstance(stem, str) or len(stem.strip()) < 10:
            err(f"{at}: stem missing or too short")
        else:
            import re

            norm = re.sub(r"[^a-z0-9]+", " ", stem.lower()).strip()
            if norm in seen_stems:
                err(f"{at}: stem duplicates {seen_stems[norm]}")
            else:
                seen_stems[norm] = qid or at

        choices = q.get("choices")
        if not isinstance(choices, list) or len(choices) < 4:
            err(f"{at}: needs at least 4 choices")
            continue

        choice_ids = [c.get("id") if isinstance(c, dict) else None for c in choices]
        if len(set(choice_ids)) != len(choice_ids):
            err(f"{at}: duplicate choice ids")
        texts = [str((c or {}).get("text") or "").strip().lower() for c in choices]
        if any(not t for t in texts):
            err(f"{at}: a choice has empty text")
        if len(set(texts)) != len(texts):
            err(f"{at}: two choices have identical text")
        for t in texts:
            if any(b in t for b in BANNED):
                warn(f'{at}: banned choice pattern ("{t}")')

        answer = q.get("answer")
        if not isinstance(answer, list) or not answer:
            err(f"{at}: answer must be a non-empty array of choice ids")
            continue
        for a in answer:
            if a not in choice_ids:
                err(f'{at}: answer "{a}" is not one of its choices')
        if q.get("type") == "single" and len(answer) != 1:
            err(f'{at}: type "single" but {len(answer)} correct answers')
        if q.get("type") == "multi" and len(answer) < 2:
            err(f'{at}: type "multi" but only 1 correct answer')

        ww = q.get("whyWrong") or {}
        for c in [c for c in choice_ids if c not in answer]:
            if not ww.get(c) or len(str(ww[c]).strip()) < 10:
                err(f'{at}: whyWrong missing or too short for choice "{c}"')
        for c in ww:
            if c in answer:
                warn(f'{at}: whyWrong has an entry for correct choice "{c}"')

        expl = q.get("explanation")
        if not isinstance(expl, str) or len(expl.strip()) < 20:
            err(f"{at}: explanation missing or too short")

        topic = q.get("topic")
        if not isinstance(topic, str) or len(topic.strip()) < 3:
            err(f"{at}: missing topic label")
        else:
            topics[topic.strip()] = topics.get(topic.strip(), 0) + 1

        if q.get("bloom") not in BLOOMS:
            err(f"{at}: bloom must be one of {', '.join(BLOOMS)}")
        else:
            bloom_count[q["bloom"]] += 1

        diff = q.get("difficulty")
        if not isinstance(diff, int) or isinstance(diff, bool) or not 1 <= diff <= 3:
            err(f"{at}: difficulty must be an integer 1-3")

        if q.get("type") == "single" and len(answer) == 1:
            singles += 1
            key_count[answer[0]] = key_count.get(answer[0], 0) + 1
            lengths = [len(str((c or {}).get("text") or "")) for c in choices]
            mx = max(lengths)
            idx = choice_ids.index(answer[0])
            if lengths[idx] == mx and lengths.count(mx) == 1:
                longest_is_answer += 1

    if singles >= 10:
        for letter, n in key_count.items():
            if n / singles > 0.35:
                warn(f'answer key skewed: "{letter}" is correct {n}/{singles} ({round(n/singles*100)}%)')
        if longest_is_answer / singles > 0.45:
            warn(
                f"length cue: the longest choice is correct {longest_is_answer}/{singles} "
                f"({round(longest_is_answer/singles*100)}%) — guessable without reading the stem"
            )

    if topics and len(qs) >= 20:
        if len(topics) < 6:
            warn(f"only {len(topics)} distinct topics — results breakdown will be coarse")
        if len(topics) > 15:
            warn(f"{len(topics)} distinct topics — too fragmented to group results by")
        singletons = [t for t, n in topics.items() if n == 1]
        if len(singletons) > 3:
            warn(f'{len(singletons)} topics have only one question (e.g. "{singletons[0]}")')

    prof = profiles.get(s.get("profile")) or {}
    mix = prof.get("mix")
    if mix and qs:
        for b in BLOOMS:
            want = (mix.get(b, 0) / 100) * len(qs)
            got = bloom_count[b]
            if abs(got - want) > max(5, len(qs) * 0.15):
                warn(f'bloom "{b}": {got} questions, profile "{s.get("profile")}" targets ~{round(want)}')

    return errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--expect", type=int, default=50)
    args = ap.parse_args()

    try:
        profiles = json.loads((ROOT / "prompts" / "profiles.json").read_text(encoding="utf-8"))
    except Exception:
        profiles = {}

    if args.files:
        files = [pathlib.Path(f) for f in args.files]
    else:
        files = sorted(p for p in (ROOT / "data").rglob("*.json") if p.name != "manifest.json")

    if not files:
        print("No question sets found under data/ yet. Nothing to validate.")
        return 0

    total_e = total_w = 0
    for f in files:
        rel = f.relative_to(ROOT).as_posix() if f.is_absolute() else f.as_posix()
        try:
            errors, warnings = validate_set(
                json.loads(f.read_text(encoding="utf-8")), profiles, args.expect
            )
        except Exception as e:
            errors, warnings = [f"not valid JSON — {e}"], []

        total_e += len(errors)
        total_w += len(warnings)
        if not errors and not warnings:
            print(f"OK   {rel}")
            continue
        print(f"{'FAIL' if errors else 'WARN'} {rel}")
        for e in errors:
            print(f"    x {e}")
        for w in warnings:
            print(f"    ! {w}")

    print(f"\n{len(files)} set(s) checked — {total_e} error(s), {total_w} warning(s).")
    return 1 if total_e else 0


if __name__ == "__main__":
    sys.exit(main())
