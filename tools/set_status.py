"""Flip a section's status in data/manifest.json.

Small, but it is the last step of every section and was otherwise an ad-hoc
script each time.

Usage
  python tools/set_status.py ch02 s09                  # -> generated
  python tools/set_status.py ch02 s09 --status pending
  python tools/set_status.py ch02 review               # the chapter review entry
"""

import argparse
import json

MANIFEST = "data/manifest.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("chapter", help="chapter id, e.g. ch02")
    ap.add_argument("section", help="section id, e.g. s09, or 'review'")
    ap.add_argument("--status", default="generated", choices=["generated", "pending", "review"])
    args = ap.parse_args()

    with open(MANIFEST, encoding="utf-8") as fh:
        data = json.load(fh)

    chapter = next((c for c in data.get("chapters", []) if c.get("id") == args.chapter), None)
    if chapter is None:
        raise SystemExit(f"no chapter {args.chapter} in {MANIFEST}")

    if args.section == "review":
        if "review" not in chapter:
            raise SystemExit(f"{args.chapter} has no review entry")
        before = chapter["review"].get("status")
        chapter["review"]["status"] = args.status
        target = f"{args.chapter} review"
    else:
        section = next((s for s in chapter.get("sections", []) if s.get("id") == args.section), None)
        if section is None:
            raise SystemExit(f"no section {args.section} in {args.chapter}")
        before = section.get("status")
        section["status"] = args.status
        target = f"{args.chapter}/{args.section}"

    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"{target}: {before} -> {args.status}")


if __name__ == "__main__":
    main()
