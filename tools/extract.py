# Turn a source PDF into something a model can read.
#
#   python tools/extract.py pdfs/Whatever.pdf     # one file
#   python tools/extract.py                       # every PDF in pdfs/
#
# Two kinds of PDF show up in this course, and they need different handling:
#
#   Digital  — a real text layer. Extracted to text/<name>.txt. Cheap, exact.
#   Scanned  — each page is one image (a printed/DRM'd textbook chapter). There
#              is nothing to extract, so pages are rendered to
#              text/<name>.pages/p001.png for Claude to read directly.
#
# The tool decides which by measuring the text layer, so you can point it at a
# folder of mixed PDFs and not think about it. Output lands in text/, which is
# gitignored — rendered pages are still the publisher's copyrighted content.

import argparse
import pathlib
import re
import shutil
import sys

try:
    import pymupdf
except ImportError:
    sys.exit("PyMuPDF is missing. Install it with:  python -m pip install pymupdf")

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "pdfs"
OUT_DIR = ROOT / "text"

# Below this many words per page, the "text layer" is just a watermark or
# running header and the page is really a scan.
WORDS_PER_PAGE_MIN = 40

# A line that is nothing but a page number, or the "12 | Chapter 3" furniture
# that repeats on every page.
NOISE = re.compile(r"^\s*(\d{1,4}|[ivxlIVXL]{1,7})\s*([|·—-]\s*.{0,60})?$")

# The print-on-demand watermark stamped onto every page of the scanned books.
WATERMARK = re.compile(r"printed by:.*?prosecuted\.", re.IGNORECASE | re.DOTALL)


def clean(text: str) -> str:
    """Undo the artifacts of PDF text extraction: watermarks, hyphens, wraps."""
    text = WATERMARK.sub("", text)
    # Word split across a line break by a hyphen: "constructiv-\nism".
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    lines = [ln.rstrip() for ln in text.split("\n")]
    kept = [ln for ln in lines if not NOISE.match(ln)]

    # Rejoin lines that a fixed-width PDF layout broke mid-sentence: previous
    # line ends mid-clause and the next starts lowercase.
    out: list[str] = []
    for ln in kept:
        if (
            out
            and out[-1]
            and ln
            and not out[-1].endswith((".", ":", ";", "?", "!"))
            and ln[:1].islower()
        ):
            out[-1] += " " + ln.lstrip()
        else:
            out.append(ln)

    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def as_text(doc, pdf_path: pathlib.Path) -> None:
    pages = []
    for i, page in enumerate(doc, start=1):
        body = clean(page.get_text("text"))
        if body:
            pages.append((i, body))

    out_path = OUT_DIR / (pdf_path.stem + ".txt")
    text = "\n\n".join(f"===== page {i} =====\n{b}" for i, b in pages) + "\n"
    out_path.write_text(text, encoding="utf-8", newline="\n")

    md_path = OUT_DIR / (pdf_path.stem + ".md")
    md = [f"# {pdf_path.stem}", "", f"Extracted from `{pdf_path.name}`.", ""]
    for i, b in pages:
        md += [f"## Page {i}", "", b, ""]
    md_path.write_text("\n".join(md), encoding="utf-8", newline="\n")

    print(f"  text layer -> text/{out_path.name} and text/{md_path.name}")
    print(f"    ({len(pages)} pages, {len(text.split()):,} words)")


def as_images(doc, pdf_path: pathlib.Path, dpi: int) -> None:
    out_dir = OUT_DIR / (pdf_path.stem + ".pages")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    for i, page in enumerate(doc, start=1):
        page.get_pixmap(dpi=dpi).save(out_dir / f"p{i:03d}.png")

    print(f"  scanned -> text/{out_dir.name}/  ({doc.page_count} pages at {dpi} dpi)")
    print("    These are images: read them directly rather than extracting text.")
    stub_markdown(pdf_path, doc.page_count)


def stub_markdown(pdf_path: pathlib.Path, pages: int) -> None:
    """
    Start the transcript file for a scanned PDF.

    Nothing here can fill in the body — the pages are images, and the only
    reader is Claude. So this lays out one heading per page for Claude to
    transcribe into, and refuses to clobber a transcript that already has
    content in it.
    """
    md_path = OUT_DIR / (pdf_path.stem + ".md")
    if md_path.exists() and "_(not yet transcribed)_" not in md_path.read_text(encoding="utf-8"):
        print(f"    transcript text/{md_path.name} already written — left alone.")
        return

    body = [
        f"# {pdf_path.stem}",
        "",
        f"Transcribed from `{pdf_path.name}` ({pages} pages).",
        "Source pages are images; this file is the readable copy.",
        "",
    ]
    for i in range(1, pages + 1):
        body += [f"## Page {i}", "", "_(not yet transcribed)_", ""]

    md_path.write_text("\n".join(body), encoding="utf-8", newline="\n")
    print(f"    transcript stub -> text/{md_path.name} (fill in per page)")


def process(pdf_path: pathlib.Path, dpi: int, force: str | None) -> None:
    doc = pymupdf.open(pdf_path)
    OUT_DIR.mkdir(exist_ok=True)

    sampled = "".join(clean(doc[i].get_text("text")) for i in range(min(5, doc.page_count)))
    words_per_page = len(sampled.split()) / max(1, min(5, doc.page_count))
    mode = force or ("text" if words_per_page >= WORDS_PER_PAGE_MIN else "images")

    print(f"{pdf_path.name}  ({doc.page_count} pages, ~{words_per_page:.0f} words/page)")
    if mode == "text":
        as_text(doc, pdf_path)
    else:
        as_images(doc, pdf_path, dpi)
    doc.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare course PDFs for question generation.")
    ap.add_argument("pdf", nargs="*", help="PDF paths (default: every PDF in pdfs/)")
    ap.add_argument("--dpi", type=int, default=170, help="render resolution for scanned PDFs")
    ap.add_argument("--mode", choices=["text", "images"], help="override the auto-detected mode")
    args = ap.parse_args()

    targets = [pathlib.Path(p) for p in args.pdf] if args.pdf else sorted(PDF_DIR.glob("*.pdf"))
    if not targets:
        sys.exit(f"No PDFs found in {PDF_DIR}")

    for pdf_path in targets:
        if not pdf_path.exists():
            print(f"skipped, not found: {pdf_path}", file=sys.stderr)
            continue
        process(pdf_path, args.dpi, args.mode)


if __name__ == "__main__":
    main()
