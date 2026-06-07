#!/usr/bin/env python3
"""Render a Markdown resume to PDF.

The script prefers high-fidelity optional tools when they are available:

1. WeasyPrint for HTML/CSS based rendering.
2. ReportLab for an offline Python fallback.
3. Pandoc when explicitly requested or discovered by --backend auto.
4. A dependency-free simple backend for basic English drafts.

No network calls are made. Photos are read from local disk only.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Sequence


BACKGROUND_CSS = """
@page {
  size: A4;
  margin: 14mm 14mm 13mm 14mm;
}
body {
  color: #111827;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
    "Noto Sans CJK SC", "Microsoft YaHei", Arial, sans-serif;
  font-size: 9.5pt;
  line-height: 1.32;
}
h1 {
  font-size: 18pt;
  margin: 0 0 5mm;
}
h2 {
  border-bottom: 0.6pt solid #d1d5db;
  font-size: 11.5pt;
  margin: 4mm 0 2mm;
  padding-bottom: 1mm;
}
h3 {
  font-size: 10.5pt;
  margin: 3mm 0 1mm;
}
p {
  margin: 0 0 1.8mm;
}
ul, ol {
  margin: 0 0 2mm 5mm;
  padding: 0;
}
li {
  margin: 0.7mm 0;
}
table {
  border-collapse: collapse;
  margin: 2mm 0;
  width: 100%;
}
td, th {
  border: 0.4pt solid #d1d5db;
  padding: 1.2mm 1.6mm;
  vertical-align: top;
}
.portrait {
  position: fixed;
  right: 0;
  top: 0;
  width: 25mm;
  height: 30mm;
  object-fit: cover;
}
.with-photo h1,
.with-photo .resume-header {
  padding-right: 32mm;
}
"""


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a Markdown resume to a one-page-oriented A4 PDF."
    )
    parser.add_argument("input", type=Path, help="Path to the source Markdown resume.")
    parser.add_argument("output", type=Path, help="Path for the output PDF.")
    parser.add_argument(
        "--language",
        choices=("en", "zh"),
        default="en",
        help="Resume language branch. zh requires --photo unless --allow-missing-photo is set.",
    )
    parser.add_argument(
        "--photo",
        type=Path,
        help="Local portrait photo to embed for Chinese resumes.",
    )
    parser.add_argument(
        "--allow-missing-photo",
        action="store_true",
        help="Allow zh rendering without a photo. Use only for drafts.",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "weasyprint", "reportlab", "pandoc", "simple"),
        default="auto",
        help="Rendering backend. auto tries WeasyPrint, ReportLab, Pandoc, then simple.",
    )
    parser.add_argument(
        "--css",
        type=Path,
        help="Optional CSS file appended after the built-in resume CSS for WeasyPrint.",
    )
    parser.add_argument(
        "--font",
        type=Path,
        help="Optional TrueType/OpenType font for ReportLab, recommended for Chinese.",
    )
    parser.add_argument(
        "--pandoc-pdf-engine",
        default="xelatex",
        help="Pandoc PDF engine to use when --backend pandoc is selected.",
    )
    return parser.parse_args(argv)


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise SystemExit(f"{label} not found: {path}")


def validate_inputs(args: argparse.Namespace) -> None:
    require_file(args.input, "Markdown input")
    if args.photo:
        require_file(args.photo, "Portrait photo")
    if args.css:
        require_file(args.css, "CSS file")
    if args.font:
        require_file(args.font, "Font file")
    if args.language == "zh" and not args.photo and not args.allow_missing_photo:
        raise SystemExit(
            "Chinese resume rendering requires --photo. "
            "Run scripts/remove_photo_background.py first if the background needs cleanup."
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)


def has_module(module_name: str) -> bool:
    try:
        __import__(module_name)
    except ImportError:
        return False
    return True


def choose_backend(requested: str) -> str:
    if requested != "auto":
        return requested
    if has_module("weasyprint"):
        return "weasyprint"
    if has_module("reportlab"):
        return "reportlab"
    if shutil.which("pandoc"):
        return "pandoc"
    return "simple"


def markdown_to_html(markdown_text: str) -> str:
    try:
        import markdown  # type: ignore

        return markdown.markdown(
            markdown_text,
            extensions=["extra", "sane_lists", "tables"],
            output_format="html5",
        )
    except ImportError:
        return minimal_markdown_to_html(markdown_text)


def minimal_markdown_to_html(markdown_text: str) -> str:
    blocks: list[str] = []
    list_items: list[str] = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            blocks.append("<ul>" + "".join(list_items) + "</ul>")
            list_items = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            flush_list()
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if heading:
            flush_list()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{inline_markup(heading.group(2))}</h{level}>")
        elif bullet:
            list_items.append(f"<li>{inline_markup(bullet.group(1))}</li>")
        else:
            flush_list()
            blocks.append(f"<p>{inline_markup(line)}</p>")
    flush_list()
    return "\n".join(blocks)


def inline_markup(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    return escaped


def photo_uri(photo: Path | None) -> str | None:
    if not photo:
        return None
    return photo.resolve().as_uri()


def render_with_weasyprint(args: argparse.Namespace, markdown_text: str) -> None:
    try:
        from weasyprint import HTML  # type: ignore
    except ImportError as exc:
        raise SystemExit("Install WeasyPrint first: pip install weasyprint markdown") from exc

    css = BACKGROUND_CSS
    if args.css:
        css += "\n" + args.css.read_text(encoding="utf-8")
    body_class = "with-photo" if args.photo else ""
    photo_html = ""
    if args.photo:
        photo_html = f'<img class="portrait" src="{photo_uri(args.photo)}" alt="portrait">'
    document = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>{css}</style>
</head>
<body class="{body_class}">
  {photo_html}
  {markdown_to_html(markdown_text)}
</body>
</html>
"""
    HTML(string=document, base_url=str(args.input.parent.resolve())).write_pdf(str(args.output))


def paragraph_style(font_name: str, size: float = 9.3, leading: float = 11.5):
    from reportlab.lib.styles import ParagraphStyle  # type: ignore
    from reportlab.lib.enums import TA_LEFT  # type: ignore

    return ParagraphStyle(
        "Resume",
        fontName=font_name,
        fontSize=size,
        leading=leading,
        alignment=TA_LEFT,
        spaceAfter=4,
    )


def render_with_reportlab(args: argparse.Namespace, markdown_text: str) -> None:
    try:
        from reportlab.lib import colors  # type: ignore
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.lib.styles import ParagraphStyle  # type: ignore
        from reportlab.lib.units import mm  # type: ignore
        from reportlab.pdfbase import pdfmetrics  # type: ignore
        from reportlab.pdfbase.ttfonts import TTFont  # type: ignore
        from reportlab.platypus import (  # type: ignore
            Image,
            ListFlowable,
            ListItem,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
        )
    except ImportError as exc:
        raise SystemExit("Install ReportLab first: pip install reportlab pillow") from exc

    font_name = "Helvetica"
    if args.font:
        font_name = "ResumeFont"
        pdfmetrics.registerFont(TTFont(font_name, str(args.font)))
    elif args.language == "zh":
        print(
            "warning: Chinese text may not render correctly without --font pointing to a CJK TTF/OTF file.",
            file=sys.stderr,
        )

    base = paragraph_style(font_name)
    h1 = ParagraphStyle(
        "H1",
        parent=base,
        fontName=font_name,
        fontSize=17,
        leading=20,
        spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=base,
        fontName=font_name,
        fontSize=11.5,
        leading=14,
        textColor=colors.HexColor("#111827"),
        borderWidth=0.4,
        borderColor=colors.HexColor("#d1d5db"),
        borderPadding=2,
        spaceBefore=6,
        spaceAfter=5,
    )
    bullet_style = paragraph_style(font_name, 9.0, 11)

    story = []
    pending_bullets = []

    def flush_bullets() -> None:
        nonlocal pending_bullets
        if pending_bullets:
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(item, bullet_style), leftIndent=4) for item in pending_bullets],
                    bulletType="bullet",
                    leftIndent=12,
                )
            )
            pending_bullets = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_bullets()
            story.append(Spacer(1, 1.2 * mm))
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if heading:
            flush_bullets()
            style = h1 if len(heading.group(1)) == 1 else h2
            story.append(Paragraph(inline_markup(heading.group(2)), style))
        elif bullet:
            pending_bullets.append(inline_markup(bullet.group(1)))
        elif line.startswith("|"):
            flush_bullets()
            story.append(Paragraph(html.escape(line), base))
        else:
            flush_bullets()
            story.append(Paragraph(inline_markup(line), base))
    flush_bullets()

    doc = SimpleDocTemplate(
        str(args.output),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=13 * mm,
        bottomMargin=12 * mm,
    )

    def draw_photo(canvas, _doc) -> None:
        if not args.photo:
            return
        try:
            image = Image(str(args.photo), width=25 * mm, height=30 * mm)
            image.drawOn(canvas, A4[0] - 14 * mm - 25 * mm, A4[1] - 13 * mm - 30 * mm)
        except Exception as exc:  # pragma: no cover - reportlab image plugin details vary.
            raise RuntimeError(f"Could not embed photo: {args.photo}") from exc

    doc.build(story, onFirstPage=draw_photo)


def render_with_pandoc(args: argparse.Namespace) -> None:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("Pandoc not found. Install pandoc or use --backend weasyprint/reportlab.")

    source = args.input
    temp_path: Path | None = None
    try:
        if args.photo:
            temp_dir = Path(tempfile.mkdtemp(prefix="career_advisor_pdf_"))
            temp_path = temp_dir / args.input.name
            temp_path.write_text(
                f'<img src="{photo_uri(args.photo)}" style="float:right;width:25mm;height:30mm;object-fit:cover;" />\n\n'
                + args.input.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            source = temp_path
        command = [
            pandoc,
            str(source),
            "-o",
            str(args.output),
            "--pdf-engine",
            args.pandoc_pdf_engine,
        ]
        subprocess.run(command, check=True)
    finally:
        if temp_path:
            try:
                temp_path.unlink()
                temp_path.parent.rmdir()
            except OSError:
                pass


def markdown_to_simple_lines(markdown_text: str) -> list[tuple[str, int]]:
    lines: list[tuple[str, int]] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append(("", 9))
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if heading:
            size = 18 if len(heading.group(1)) == 1 else 13
            lines.append((strip_inline_markup(heading.group(2)), size))
        elif bullet:
            lines.append((f"- {strip_inline_markup(bullet.group(1))}", 9))
        elif line.startswith("|"):
            lines.append((strip_inline_markup(line), 8))
        else:
            lines.append((strip_inline_markup(line), 9))
    return lines


def strip_inline_markup(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text


def wrap_text(text: str, max_chars: int) -> Iterable[str]:
    if len(text) <= max_chars:
        yield text
        return
    words = text.split()
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            yield current
            current = word
        else:
            current = candidate
    if current:
        yield current


def pdf_escape(text: str) -> str:
    latin = text.encode("latin-1", "replace").decode("latin-1")
    return latin.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def render_with_simple(args: argparse.Namespace, markdown_text: str) -> None:
    if args.photo:
        raise SystemExit(
            "The simple backend cannot embed photos. Install WeasyPrint or ReportLab for Chinese resumes."
        )
    if args.language == "zh":
        print(
            "warning: simple backend uses built-in PDF fonts and is not suitable for Chinese glyphs.",
            file=sys.stderr,
        )

    page_width = 595
    page_height = 842
    left = 42
    top = 800
    bottom = 42
    max_chars = 96
    pages: list[list[str]] = [[]]
    y = top

    for text, size in markdown_to_simple_lines(markdown_text):
        wrapped = list(wrap_text(text, max_chars)) or [""]
        for wrapped_line in wrapped:
            leading = max(size + 3, 12)
            if y < bottom:
                pages.append([])
                y = top
            if wrapped_line:
                pages[-1].append(
                    f"BT /F1 {size} Tf {left} {y} Td ({pdf_escape(wrapped_line)}) Tj ET\n"
                )
            y -= leading

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"")  # pages object placeholder
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids: list[int] = []

    for page in pages:
        stream = "".join(page).encode("latin-1", "replace")
        content_id = len(objects) + 1
        objects.append(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        )
        page_id = len(objects) + 1
        page_ids.append(page_id)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode(
                "ascii"
            )
        )

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")
    write_pdf_objects(args.output, objects)


def write_pdf_objects(output: Path, objects: Sequence[bytes]) -> None:
    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(data))
        data.extend(f"{index} 0 obj\n".encode("ascii"))
        data.extend(obj)
        data.extend(b"\nendobj\n")
    xref_offset = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    data.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    data.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    output.write_bytes(data)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    validate_inputs(args)
    backend = choose_backend(args.backend)
    markdown_text = args.input.read_text(encoding="utf-8")
    if backend == "weasyprint":
        render_with_weasyprint(args, markdown_text)
    elif backend == "reportlab":
        render_with_reportlab(args, markdown_text)
    elif backend == "pandoc":
        render_with_pandoc(args)
    elif backend == "simple":
        render_with_simple(args, markdown_text)
    else:  # pragma: no cover - argparse/choose_backend prevent this.
        raise SystemExit(f"Unsupported backend: {backend}")
    print(f"PDF written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
