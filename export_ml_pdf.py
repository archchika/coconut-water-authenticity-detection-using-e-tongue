"""
Export ML_1 + ML_2 model docs, full source code, and full training datasets to PDF.
Layout: white page with wide edge margins; details on white; code only in black panels.
"""
from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, white, black
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    Flowable,
    PageBreak,
    Preformatted,
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "frontend" / "ML-Models-Full-Documentation.pdf"
if not (ROOT / "frontend").exists():
    OUT = ROOT / "ML-Models-Full-Documentation.pdf"

PAGE_W, PAGE_H = A4
# Wide white edges + breathing room
MARGIN_L = 22 * mm
MARGIN_R = 22 * mm
MARGIN_T = 18 * mm
MARGIN_B = 16 * mm
# Extra white "middle" inset around content blocks
INNER_GAP = 6 * mm

BG_PAGE = HexColor("#FFFFFF")
BG_CODE = HexColor("#0A0A0C")
FG_CODE = HexColor("#E8E8EA")
FG_CODE_MUTED = HexColor("#9A9AA3")
FG_TITLE = HexColor("#111111")
FG_BODY = HexColor("#222222")
FG_META = HexColor("#555555")
LINE = HexColor("#DDDDDD")
ACCENT = HexColor("#1A1A1A")


def wrap_code_lines(text: str, width: float, pad_x: int = 10) -> list[str]:
    text = text.replace("\t", "    ")
    max_chars = max(40, int((width - 2 * pad_x) / 4.2))
    wrapped: list[str] = []
    for line in (text.splitlines() or [""]):
        if len(line) <= max_chars:
            wrapped.append(line)
        else:
            while line:
                wrapped.append(line[:max_chars])
                line = line[max_chars:]
    return wrapped


def code_blocks(text: str, width: float, title: str, max_lines: int = 55) -> list:
    """Split long source into multiple black code panels that fit a page."""
    lines = wrap_code_lines(text, width)
    blocks: list = []
    for i in range(0, len(lines), max_lines):
        chunk = lines[i : i + max_lines]
        part_title = title if i == 0 else f"{title}  (cont.)"
        blocks.append(CodeBlock(chunk, width, title=part_title))
        blocks.append(Spacer(1, 4))
    return blocks


class CodeBlock(Flowable):
    """Black-background code panel (only place black fill is used)."""

    def __init__(self, lines: list[str], width: float, title: str | None = None):
        super().__init__()
        self.lines = lines
        self.block_width = width
        self.title = title
        self.pad_x = 10
        self.pad_y = 10
        self.line_h = 10
        self.font_size = 7
        self.title_h = 16 if title else 0
        self.height = (
            self.pad_y * 2
            + self.title_h
            + max(1, len(self.lines)) * self.line_h
            + 4
        )

    def wrap(self, availWidth, availHeight):
        self.width = self.block_width
        return self.block_width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(BG_CODE)
        c.roundRect(0, 0, self.block_width, self.height, 4, fill=1, stroke=0)
        y = self.height - self.pad_y
        if self.title:
            c.setFillColor(FG_CODE_MUTED)
            c.setFont("Courier", 7)
            safe_title = self.title.encode("latin-1", "replace").decode("latin-1")
            c.drawString(self.pad_x, y - 10, safe_title)
            y -= self.title_h
        c.setFillColor(FG_CODE)
        c.setFont("Courier", self.font_size)
        for line in self.lines:
            y -= self.line_h
            if y < self.pad_y - 2:
                break
            safe = line.encode("latin-1", "replace").decode("latin-1")
            c.drawString(self.pad_x, y, safe)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_csv_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def make_styles():
    return {
        "h1": ParagraphStyle(
            "h1",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=FG_TITLE,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=FG_TITLE,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=FG_TITLE,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=FG_BODY,
            spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=FG_META,
            spaceAfter=3,
        ),
        "label": ParagraphStyle(
            "label",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=FG_TITLE,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=FG_META,
            alignment=1,
        ),
    }


def info_table(pairs: list[tuple[str, str]], width: float) -> Table:
    data = [[Paragraph(f"<b>{k}</b>", ParagraphStyle("k", fontName="Helvetica", fontSize=8.5, textColor=FG_TITLE)),
            Paragraph(v, ParagraphStyle("v", fontName="Helvetica", fontSize=8.5, textColor=FG_BODY, leading=11))]
           for k, v in pairs]
    col0 = width * 0.32
    col1 = width * 0.68
    t = Table(data, colWidths=[col0, col1])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
                ("BACKGROUND", (0, 0), (0, -1), HexColor("#F7F7F7")),
            ]
        )
    )
    return t


def dataset_table(headers: list[str], rows: list[list[str]], width: float) -> list:
    """Chunk full dataset into white tables (not black)."""
    # Fit columns
    n = len(headers)
    # Prefer key numeric columns; truncate very wide string cols
    col_w = width / max(n, 1)
    styles_h = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=6.5, textColor=FG_TITLE, leading=8)
    styles_c = ParagraphStyle("td", fontName="Courier", fontSize=6, textColor=FG_BODY, leading=7.5)

    def cell(text: str, header: bool = False) -> Paragraph:
        safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if len(safe) > 28:
            safe = safe[:27] + "…"
        return Paragraph(safe, styles_h if header else styles_c)

    flows = []
    chunk = 45
    for start in range(0, len(rows), chunk):
        part = rows[start : start + chunk]
        data = [[cell(h, True) for h in headers]]
        for r in part:
            # pad/truncate to header length
            rr = (r + [""] * n)[:n]
            data.append([cell(c) for c in rr])
        t = Table(data, colWidths=[col_w] * n, repeatRows=1)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, -1), white),
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F0F0F0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("BOX", (0, 0), (-1, -1), 0.4, LINE),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ]
        # subtle zebra on white
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), HexColor("#FAFAFA")))
        t.setStyle(TableStyle(style_cmds))
        note = Paragraph(
            f"Rows {start + 1}–{start + len(part)} of {len(rows)}",
            ParagraphStyle("rn", fontName="Helvetica", fontSize=7.5, textColor=FG_META, spaceBefore=2, spaceAfter=6),
        )
        flows.extend([t, note, Spacer(1, INNER_GAP)])
    return flows


def add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG_PAGE)
    # ensure page stays white (no dark theme)
    canvas.setFillColor(FG_META)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(PAGE_W / 2, 10 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    # thin guide lines marking white edge bands
    canvas.line(MARGIN_L - 4, MARGIN_B - 2, MARGIN_L - 4, PAGE_H - MARGIN_T + 2)
    canvas.line(PAGE_W - MARGIN_R + 4, MARGIN_B - 2, PAGE_W - MARGIN_R + 4, PAGE_H - MARGIN_T + 2)
    canvas.restoreState()


def build():
    styles = make_styles()
    content_w = PAGE_W - MARGIN_L - MARGIN_R

    story: list = []

    # ---- Cover / overview (white) ----
    story.append(Paragraph("Coconut Water ML Models — Full Documentation", styles["h1"]))
    story.append(
        Paragraph(
            "Complete model type details, full source code (black panels only), and full training datasets "
            "on a white page layout with wide left/right margins and spacing between sections.",
            styles["body"],
        )
    )
    story.append(Spacer(1, INNER_GAP))
    story.append(Paragraph("System overview", styles["h2"]))
    story.append(
        info_table(
            [
                ("Project", "Ceylon coconut-water authenticity / composition prediction"),
                ("ML libraries", "scikit-learn, pandas, numpy, joblib"),
                ("Model family", "RandomForestRegressor (ensemble of decision trees)"),
                ("Modules", "ML_1 (acids) + ML_2 (sugar)"),
                ("Train / test split", "80% train / 20% test, random_state=42"),
                ("Authenticity", "Rule-based natural-range check (not a classifier)"),
            ],
            content_w,
        )
    )
    story.append(Spacer(1, INNER_GAP * 1.5))

    # ========== ML_1 ==========
    story.append(Paragraph("1. ML_1 — Acid model (citric &amp; ascorbic)", styles["h2"]))
    story.append(Paragraph("Model type &amp; configuration", styles["h3"]))
    story.append(
        info_table(
            [
                ("Model type", "Multi-output RandomForestRegressor (scikit-learn)"),
                ("Saved artifact", "ML_1/models/random_forest_ph_temp.pkl"),
                ("Hyperparameters", "n_estimators=300, max_depth=12, min_samples_leaf=2, random_state=42"),
                ("Input features", "pH, temperature_C"),
                ("Output targets", "citric_percent_wv, ascorbic_percent_wv"),
                ("Training CSV", "ML_1/dataset/combined_pH_temp_600.csv (600 rows)"),
                ("Data origin", "Literature maturation curves → synthetic combined dataset"),
            ],
            content_w,
        )
    )
    story.append(Spacer(1, INNER_GAP))

    ml1_files = [
        ("ML_1/load_dataset.py", ROOT / "ML_1" / "load_dataset.py"),
        ("ML_1/merge_datasets.py", ROOT / "ML_1" / "merge_datasets.py"),
        ("ML_1/train_model.py", ROOT / "ML_1" / "train_model.py"),
        ("ML_1/predict.py", ROOT / "ML_1" / "predict.py"),
    ]
    story.append(Paragraph("Full source code — ML_1", styles["h3"]))
    story.append(
        Paragraph(
            "Code appears only inside black panels below. Surrounding page, margins, and headings stay white.",
            styles["meta"],
        )
    )
    for title, path in ml1_files:
        story.append(Spacer(1, 4))
        story.append(Paragraph(title, styles["label"]))
        story.append(Spacer(1, 3))
        story.extend(code_blocks(read_text(path), content_w, title=title))
        story.append(Spacer(1, INNER_GAP))  # white middle/section gap

    story.append(PageBreak())
    story.append(Paragraph("ML_1 full training dataset", styles["h2"]))
    story.append(
        Paragraph(
            "File: <b>ML_1/dataset/combined_pH_temp_600.csv</b> — all 600 training rows (white table surface).",
            styles["body"],
        )
    )
    h1, r1 = read_csv_rows(ROOT / "ML_1" / "dataset" / "combined_pH_temp_600.csv")
    story.extend(dataset_table(h1, r1, content_w))

    # ========== ML_2 ==========
    story.append(PageBreak())
    story.append(Paragraph("2. ML_2 — Sugar model", styles["h2"]))
    story.append(Paragraph("Model type &amp; configuration", styles["h3"]))
    story.append(
        info_table(
            [
                ("Model type", "Single-output RandomForestRegressor (scikit-learn)"),
                ("Saved artifact", "ML_2/models/random_forest_sugar_sensors.pkl"),
                ("Hyperparameters", "n_estimators=200, max_depth=12, random_state=42"),
                ("Input features", "pH, TDS, temperature, turbidity"),
                ("Output target", "sugar_pct (Brix)"),
                ("Training CSV", "ML_2/dataset/combined_sensors_sugar.csv (482 rows)"),
                ("Data origin", "400 literature Brix–TDS rows + 82 calibration samples"),
            ],
            content_w,
        )
    )
    story.append(Spacer(1, INNER_GAP))

    ml2_files = [
        ("ML_2/load_dataset.py", ROOT / "ML_2" / "load_dataset.py"),
        ("ML_2/merge_datasets.py", ROOT / "ML_2" / "merge_datasets.py"),
        ("ML_2/train_model.py", ROOT / "ML_2" / "train_model.py"),
        ("ML_2/predict.py", ROOT / "ML_2" / "predict.py"),
    ]
    story.append(Paragraph("Full source code — ML_2", styles["h3"]))
    story.append(
        Paragraph(
            "Code appears only inside black panels below. Surrounding page, margins, and headings stay white.",
            styles["meta"],
        )
    )
    for title, path in ml2_files:
        story.append(Spacer(1, 4))
        story.append(Paragraph(title, styles["label"]))
        story.append(Spacer(1, 3))
        story.extend(code_blocks(read_text(path), content_w, title=title))
        story.append(Spacer(1, INNER_GAP))

    story.append(PageBreak())
    story.append(Paragraph("ML_2 full training dataset", styles["h2"]))
    story.append(
        Paragraph(
            "File: <b>ML_2/dataset/combined_sensors_sugar.csv</b> — all training rows (white table surface).",
            styles["body"],
        )
    )
    h2, r2 = read_csv_rows(ROOT / "ML_2" / "dataset" / "combined_sensors_sugar.csv")
    story.extend(dataset_table(h2, r2, content_w))

    # Frame with white edges
    frame = Frame(
        MARGIN_L,
        MARGIN_B,
        content_w,
        PAGE_H - MARGIN_T - MARGIN_B,
        leftPadding=INNER_GAP / 2,
        rightPadding=INNER_GAP / 2,
        topPadding=4,
        bottomPadding=4,
        id="normal",
    )
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        title="ML Models Full Documentation",
        author="Ceylon Coconut Research",
    )
    doc.addPageTemplates([PageTemplate(id="white", frames=[frame], onPage=add_footer)])
    doc.build(story)
    print(f"Wrote {OUT}")
    print(f"ML_1 rows: {len(r1)}, ML_2 rows: {len(r2)}")


if __name__ == "__main__":
    build()
