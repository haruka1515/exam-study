"""One-shot migration: the four-level Bloom ladder -> the EPPP's two levels.

The EPPP tests recall and application only (Orientation chapter, Table 5), so
`bloom` becomes `level`:  recall/understand -> recall, apply/analyze -> application.

This is lossy and deliberately so — "understand" was never an EPPP category. It
preserves each set's rough recall/application split so the files stay valid and
playable; it does not fix a set whose split is wrong for its domain. That needs
regeneration.

Usage:  python tools/migrate_levels.py [files...]      (default: data/ch*/s*.json)
"""

import glob
import json
import sys

MAP = {
    "recall": "recall",
    "understand": "recall",
    "apply": "application",
    "analyze": "application",
}


def migrate(path: str) -> bool:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    changed = 0
    for q in data.get("questions", []):
        if "bloom" in q:
            # Rebuild the dict so `level` lands where `bloom` was, keeping key order.
            items = [(("level", MAP[v]) if k == "bloom" else (k, v)) for k, v in q.items()]
            q.clear()
            q.update(items)
            changed += 1

    if not changed:
        print(f"  {path}: nothing to migrate")
        return False

    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"  {path}: {changed} questions migrated")
    return True


def main() -> None:
    paths = sys.argv[1:] or sorted(glob.glob("data/ch*/s*.json"))
    if not paths:
        sys.exit("no question sets found")
    print(f"Migrating {len(paths)} set(s):")
    for p in paths:
        migrate(p)


if __name__ == "__main__":
    main()
