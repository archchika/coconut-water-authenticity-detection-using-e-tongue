"""
Export ML_1 + ML_2 model docs, full source code, and full training datasets to Word (.docx).
Layout: white page with wide margins; details on white; code only in black shading.
"""
from __future__ import annotations

import csv
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Twips

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "frontend" / "ML-Models-Full-Documentation.docx"
if not (ROOT / "frontend").exists():
    OUT = ROOT / "ML-Models-Full-Documentation.docx"

CODE_BG = "0A0A0C"
CODE_FG = RGBColor(0xE8, 0xE8, 0xEA)
TITLE_FG = RGBColor(0x11, 0x11, 0x11)
BODY_FG = RGBColor(0x22, 0x22, 0x22)
META_FG = RGBColor(0x55, 0x55, 0x55)
HEADER_BG = "F0F0F0"
LABEL_BG = "F7F7F7"


def set_run_font(run, name="Calibri", size=10, bold=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def set_cell_shading(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_paragraph_shading(paragraph, hex_color: str):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    pPr.append(shd)


def add_heading(doc: Document, text: str, level: int = 1):
    sizes = {1: 18, 2: 14, 3: 12}
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12 if level > 1 else 0)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    set_run_font(run, "Calibri", sizes.get(level, 12), bold=True, color=TITLE_FG)
    return p


def add_body(doc: Document, text: str, size: int = 10, color=BODY_FG):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    set_run_font(run, "Calibri", size, color=color)
    return p


def add_info_table(doc: Document, pairs: list[tuple[str, str]]):
    table = doc.add_table(rows=len(pairs), cols=2)
    table.style = "Table Grid"
    for i, (k, v) in enumerate(pairs):
        c0, c1 = table.rows[i].cells
        c0.text = ""
        c1.text = ""
        r0 = c0.paragraphs[0].add_run(k)
        set_run_font(r0, "Calibri", 9, bold=True, color=TITLE_FG)
        r1 = c1.paragraphs[0].add_run(v)
        set_run_font(r1, "Calibri", 9, color=BODY_FG)
        set_cell_shading(c0, LABEL_BG)
        # white surface for values
        set_cell_shading(c1, "FFFFFF")
    doc.add_paragraph()


def add_code_block(doc: Document, title: str, code: str):
    label = doc.add_paragraph()
    label.paragraph_format.space_before = Pt(8)
    label.paragraph_format.space_after = Pt(2)
    lr = label.add_run(title)
    set_run_font(lr, "Calibri", 9, bold=True, color=TITLE_FG)

    # Black background only for code lines
    for line in code.replace("\t", "    ").splitlines() or [""]:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        set_paragraph_shading(p, CODE_BG)
        # keep a little left indent so code sits inset (white edge feel)
        p.paragraph_format.left_indent = Cm(0.3)
        p.paragraph_format.right_indent = Cm(0.3)
        run = p.add_run(line if line else " ")
        set_run_font(run, "Consolas", 8, color=CODE_FG)

    # white spacer after code
    gap = doc.add_paragraph()
    gap.paragraph_format.space_before = Pt(8)
    gap.paragraph_format.space_after = Pt(8)


def add_dataset_table(doc: Document, headers: list[str], rows: list[list[str]], caption: str):
    add_heading(doc, caption, level=2)
    add_body(
        doc,
        f"Full training data ({len(rows)} rows) on white table surface.",
        size=9,
        color=META_FG,
    )

    # Word tables get heavy with many columns; keep all columns but small font
    n = len(headers)
    # chunk rows for manageable table sizes in Word
    chunk = 80
    for start in range(0, len(rows), chunk):
        part = rows[start : start + chunk]
        add_body(
            doc,
            f"Rows {start + 1}–{start + len(part)} of {len(rows)}",
            size=8,
            color=META_FG,
        )
        table = doc.add_table(rows=1 + len(part), cols=n)
        table.style = "Table Grid"

        for j, h in enumerate(headers):
            cell = table.rows[0].cells[j]
            cell.text = ""
            run = cell.paragraphs[0].add_run(h)
            set_run_font(run, "Calibri", 7, bold=True, color=TITLE_FG)
            set_cell_shading(cell, HEADER_BG)

        for ri, row in enumerate(part):
            rr = (row + [""] * n)[:n]
            for j, val in enumerate(rr):
                cell = table.rows[ri + 1].cells[j]
                cell.text = ""
                text = val if len(val) <= 40 else val[:39] + "…"
                run = cell.paragraphs[0].add_run(text)
                set_run_font(run, "Consolas", 6.5, color=BODY_FG)
                set_cell_shading(cell, "FFFFFF" if ri % 2 == 0 else "FAFAFA")

        # white middle space between chunks
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_before = Pt(10)
        spacer.paragraph_format.space_after = Pt(10)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_csv_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def build():
    doc = Document()

    # Wide white margins (edges)
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(1.8)
        section.left_margin = Cm(2.4)
        section.right_margin = Cm(2.4)

    add_heading(doc, "Coconut Water ML Models — Full Documentation", 1)
    add_body(
        doc,
        "Complete model type details, full source code (black panels only), and full training "
        "datasets on a white page layout with wide left/right margins and spacing between sections.",
    )

    add_heading(doc, "System overview", 2)
    add_info_table(
        doc,
        [
            ("Project", "Ceylon coconut-water authenticity / composition prediction"),
            ("ML libraries", "scikit-learn, pandas, numpy, joblib"),
            ("Model family", "RandomForestRegressor (ensemble of decision trees)"),
            ("Modules", "ML_1 (acids) + ML_2 (sugar)"),
            ("Train / test split", "80% train / 20% test, random_state=42"),
            ("Authenticity", "Rule-based natural-range check (not a classifier)"),
        ],
    )

    # ---- ML_1 ----
    add_heading(doc, "1. ML_1 — Acid model (citric & ascorbic)", 2)
    add_heading(doc, "Model type & configuration", 3)
    add_info_table(
        doc,
        [
            ("Model type", "Multi-output RandomForestRegressor (scikit-learn)"),
            ("Saved artifact", "ML_1/models/random_forest_ph_temp.pkl"),
            (
                "Hyperparameters",
                "n_estimators=300, max_depth=12, min_samples_leaf=2, random_state=42",
            ),
            ("Input features", "pH, temperature_C"),
            ("Output targets", "citric_percent_wv, ascorbic_percent_wv"),
            ("Training CSV", "ML_1/dataset/combined_pH_temp_600.csv (600 rows)"),
            ("Data origin", "Literature maturation curves → synthetic combined dataset"),
        ],
    )

    add_heading(doc, "Full source code — ML_1", 3)
    add_body(
        doc,
        "Code appears only inside black panels below. Surrounding page, margins, and headings stay white.",
        size=9,
        color=META_FG,
    )
    ml1_files = [
        ("ML_1/load_dataset.py", ROOT / "ML_1" / "load_dataset.py"),
        ("ML_1/merge_datasets.py", ROOT / "ML_1" / "merge_datasets.py"),
        ("ML_1/train_model.py", ROOT / "ML_1" / "train_model.py"),
        ("ML_1/predict.py", ROOT / "ML_1" / "predict.py"),
    ]
    for title, path in ml1_files:
        add_code_block(doc, title, read_text(path))

    h1, r1 = read_csv_rows(ROOT / "ML_1" / "dataset" / "combined_pH_temp_600.csv")
    add_dataset_table(
        doc,
        h1,
        r1,
        "ML_1 full training dataset (combined_pH_temp_600.csv)",
    )

    # ---- ML_2 ----
    doc.add_page_break()
    add_heading(doc, "2. ML_2 — Sugar model", 2)
    add_heading(doc, "Model type & configuration", 3)
    add_info_table(
        doc,
        [
            ("Model type", "Single-output RandomForestRegressor (scikit-learn)"),
            ("Saved artifact", "ML_2/models/random_forest_sugar_sensors.pkl"),
            ("Hyperparameters", "n_estimators=200, max_depth=12, random_state=42"),
            ("Input features", "pH, TDS, temperature, turbidity"),
            ("Output target", "sugar_pct (Brix)"),
            ("Training CSV", "ML_2/dataset/combined_sensors_sugar.csv (482 rows)"),
            ("Data origin", "400 literature Brix–TDS rows + 82 calibration samples"),
        ],
    )

    add_heading(doc, "Full source code — ML_2", 3)
    add_body(
        doc,
        "Code appears only inside black panels below. Surrounding page, margins, and headings stay white.",
        size=9,
        color=META_FG,
    )
    ml2_files = [
        ("ML_2/load_dataset.py", ROOT / "ML_2" / "load_dataset.py"),
        ("ML_2/merge_datasets.py", ROOT / "ML_2" / "merge_datasets.py"),
        ("ML_2/train_model.py", ROOT / "ML_2" / "train_model.py"),
        ("ML_2/predict.py", ROOT / "ML_2" / "predict.py"),
    ]
    for title, path in ml2_files:
        add_code_block(doc, title, read_text(path))

    h2, r2 = read_csv_rows(ROOT / "ML_2" / "dataset" / "combined_sensors_sugar.csv")
    add_dataset_table(
        doc,
        h2,
        r2,
        "ML_2 full training dataset (combined_sensors_sugar.csv)",
    )

    doc.save(str(OUT))
    print(f"Wrote {OUT}")
    print(f"ML_1 rows: {len(r1)}, ML_2 rows: {len(r2)}")


if __name__ == "__main__":
    build()
