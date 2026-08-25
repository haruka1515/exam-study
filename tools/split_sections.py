# Split a rendered chapter into one folder of page images per section.
#
#   python tools/split_sections.py text/Ethics.pages sections/Ethics.json
#
# A long chapter is one PDF but many question sets, and a question set is
# generated per section. This copies each section's pages into
# text/<name>.s01/, text/<name>.s02/, ... and writes a matching .md stub, so
# each section can be transcribed and generated independently.
#
# The spec JSON describes where the sections start, using the page numbers
# PRINTED on the page (which is what a table of contents lists), plus the
# offset between those and the PDF's own page numbering:
#
#   {
#     "name": "Ethics",
#     "offset": 53,                  // pdf_page = printed_page - offset
#     "lastPrintedPage": 137,        // last page of the final section
#     "sections": [
#       { "number": 1, "id": "s01", "title": "Introduction", "startPrinted": 57 },
#       ...
#     ]
#   }
#
# Each section runs from its own start page up to the page before the next
# section starts, so the boundaries come from the table of contents alone.

import argparse
import json
import pathlib
import shutil
import sys


def main():
    ap = argparse.ArgumentParser(description="Split rendered chapter pages into sections.")
    ap.add_argument("pages_dir", help="the .pages directory written by tools/extract.py")
    ap.add_argument("spec", help="JSON describing the section boundaries")
    ap.add_argument("--dry-run", action="store_true", help="print the plan without copying")
    args = ap.parse_args()

    pages_dir = pathlib.Path(args.pages_dir)
    if not pages_dir.is_dir():
        sys.exit(f"not a directory: {pages_dir}")

    spec = json.loads(pathlib.Path(args.spec).read_text(encoding="utf-8"))
    offset = spec["offset"]
    sections = sorted(spec["sections"], key=lambda s: s["startPrinted"])
    out_root = pages_dir.parent
    name = spec["name"]

    available = sorted(pages_dir.glob("p*.png"))
    if not available:
        sys.exit(f"no page images in {pages_dir}")
    last_pdf_page = int(available[-1].stem[1:])

    # Each section ends where the next one begins.
    plan = []
    for i, sec in enumerate(sections):
        start_pdf = sec["startPrinted"] - offset
        if i + 1 < len(sections):
            end_pdf = sections[i + 1]["startPrinted"] - offset - 1
        else:
            end_pdf = spec.get("lastPrintedPage", 0) - offset or last_pdf_page
        end_pdf = min(end_pdf, last_pdf_page)
        plan.append((sec, start_pdf, end_pdf))

    for sec, start_pdf, end_pdf in plan:
        n = end_pdf - start_pdf + 1
        printed = f"pp. {sec['startPrinted']}-{sec['startPrinted'] + n - 1}"
        print(f"  {sec['id']}  pdf {start_pdf:>3}-{end_pdf:<3} ({n:>2} pages, {printed})  {sec['title']}")
        if args.dry_run:
            continue
        if n < 1:
            print(f"    ! {sec['id']} has no pages — check startPrinted values")
            continue

        dest = out_root / f"{name}.{sec['id']}"
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)

        for pdf_page in range(start_pdf, end_pdf + 1):
            src = pages_dir / f"p{pdf_page:03d}.png"
            if src.exists():
                shutil.copy2(src, dest / f"p{sec['startPrinted'] + pdf_page - start_pdf:03d}.png")
            else:
                print(f"    ! missing {src.name}")

        write_stub(out_root, name, sec, start_pdf, end_pdf, offset)

    total = sum(e - s + 1 for _, s, e in plan)
    print(f"\n{len(plan)} sections, {total} pages of {last_pdf_page}.")
    if not args.dry_run:
        print(f"Transcribe each into {out_root.as_posix()}/{name}.<id>.md")
    return 0


def write_stub(out_root, name, sec, start_pdf, end_pdf, offset):
    """One markdown file per section, headed per page, for Claude to fill in."""
    md = out_root / f"{name}.{sec['id']}.md"
    if md.exists() and "_(not yet transcribed)_" not in md.read_text(encoding="utf-8"):
        return

    body = [
        f"# {name} — {sec['number']}. {sec['title']}",
        "",
        f"Section {sec['number']} of `{name}.pdf`, printed pages "
        f"{sec['startPrinted']}-{sec['startPrinted'] + end_pdf - start_pdf}.",
        f"Page images: `{name}.{sec['id']}/`",
        "",
    ]
    for pdf_page in range(start_pdf, end_pdf + 1):
        body += [f"## Page {pdf_page + offset}", "", "_(not yet transcribed)_", ""]

    md.write_text("\n".join(body), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.exit(main())
