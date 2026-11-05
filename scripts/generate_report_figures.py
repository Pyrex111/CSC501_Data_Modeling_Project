"""Build the exact architecture and cropped UI evidence used in the M4 report.

Screenshot pixels are not rewritten: PDF clips position the committed captures.
All nine originals remain supplementary files. Poppler's pdftoppm is optional
and refreshes the PNG architecture preview. Install requirements.txt first.
"""
from __future__ import annotations
import argparse
import math
from pathlib import Path
import shutil
import subprocess
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / 'milestones/04_relational/figures'


def arrow(c, points, dashed=False):
    c.saveState()
    c.setStrokeColor(HexColor('#38556e'))
    c.setFillColor(HexColor('#38556e'))
    c.setLineWidth(.8)
    if dashed:
        c.setDash(3, 2)
    p = c.beginPath()
    p.moveTo(*points[0])
    for point in points[1:]:
        p.lineTo(*point)
    c.drawPath(p)
    c.setDash()
    x, y = points[-1]
    px, py = points[-2]
    angle = math.atan2(y - py, x - px)
    p = c.beginPath()
    p.moveTo(x, y)
    for offset in (2.65, -2.65):
        p.lineTo(x + 4 * math.cos(angle + offset),
                 y + 4 * math.sin(angle + offset))
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def box(c, x, y, width, height, title, lines, fill):
    c.setFillColor(HexColor(fill))
    c.setStrokeColor(HexColor('#38556e'))
    c.roundRect(x, y, width, height, 4, fill=1)
    c.setFillColor(HexColor('#172a3a'))
    c.setFont('Helvetica-Bold', 8)
    c.drawCentredString(x + width / 2, y + height - 12, title)
    c.setFont('Helvetica', 7.4)
    for i, line in enumerate(lines):
        c.drawCentredString(x + width / 2, y + height - 23 - i * 9, line)


def architecture(output):
    c = canvas.Canvas(str(output), pagesize=(270, 200), invariant=1)
    c.setTitle('System architecture: actual request and validation calls')
    box(c, 5, 150, 260, 44, 'UI: Flask routes and HTML templates',
        ['Opens a Database connection; renders forms, results and errors'], '#eaf2fb')
    box(c, 5, 78, 110, 49, 'Business helpers',
        ['Parse and check input', 'Build payloads; explain errors'], '#fff3de')
    box(c, 145, 78, 120, 49, 'DAL: repositories / lookups',
        ['Receives the request connection', 'Runs parameterized SQL'], '#edf6ed')
    box(c, 5, 6, 110, 49, 'Transaction validator',
        ['validated_transaction', 'Checks the proposed final state'], '#edf6ed')
    box(c, 145, 6, 120, 49, 'SQLite persistence',
        ['12 tables, 13 FKs, 4 triggers', 'Types, keys and scalar checks'], '#f2edf8')
    arrow(c, [(58, 150), (58, 127)])
    arrow(c, [(205, 150), (205, 127)])
    arrow(c, [(145, 102), (130, 102), (130, 31), (115, 31)])
    arrow(c, [(210, 78), (210, 55)])
    arrow(c, [(115, 21), (145, 21)], dashed=True)
    c.setFillColor(HexColor('#172a3a'))
    c.setFont('Helvetica', 7)
    c.drawString(5, 137, 'parse / check')
    c.drawString(147, 137, 'connection + calls')
    c.drawString(86, 62, 'writes')
    c.drawString(216, 63, 'SQL')
    c.setFont('Helvetica', 6.3)
    c.drawCentredString(130, 9, 'state')
    c.showPage()
    c.save()


def clip(c, path, rectangle, x, top, width):
    """Place an unchanged screenshot excerpt; rectangle is top-left pixels."""
    left, upper, right, lower = rectangle
    with Image.open(path) as im:
        iw, ih = im.size
    scale = width / (right - left)
    height = (lower - upper) * scale
    c.saveState()
    p = c.beginPath()
    p.rect(x, top - height, width, height)
    c.clipPath(p, stroke=0)
    c.drawImage(ImageReader(str(path)), x - left * scale,
                top - (ih - upper) * scale, width=iw * scale, height=ih * scale)
    c.restoreState()
    return top - height


def ui_evidence(output, screenshots):
    c = canvas.Canvas(str(output), pagesize=(540, 342), invariant=1)
    c.setTitle('UI evidence: unchanged excerpts of synthetic application captures')
    c.setFillColor(HexColor('#172a3a'))
    c.setFont('Helvetica-Bold', 10)
    c.drawString(0, 330, '(a) Search: Geography filter and results')
    c.drawString(280, 330, '(b) Create: saved Partial disclosure')
    clip(c, screenshots / '01_search_geography_filter.png',
         (35, 140, 695, 370), 0, 319, 260)
    p = screenshots / '04_create_partial_disclosure_saved.png'
    top = clip(c, p, (40, 95, 560, 183), 280, 319, 260)
    clip(c, p, (40, 279, 560, 395), 280, top - 5, 260)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(0, 195, '(c) Update: batch saved; total remains 1')
    c.drawString(280, 195, '(d) Delete: two entries remain; total 0.7')
    p = screenshots / '07_update_batch_saved.png'
    top = clip(c, p, (40, 95, 560, 135), 0, 184, 260)
    top = clip(c, p, (650, 766, 1060, 946), 0, top - 5, 260)
    clip(c, p, (650, 1157, 1060, 1195), 0, top - 5, 260)
    p = screenshots / '09_delete_saved_partial.png'
    top = clip(c, p, (40, 95, 560, 135), 280, 184, 260)
    clip(c, p, (650, 766, 1060, 982), 280, top - 5, 260)
    c.showPage()
    c.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=FIGURES)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    arch = args.output_dir / 'system_architecture.pdf'
    architecture(arch)
    ui_evidence(args.output_dir / 'ui_operations.pdf', FIGURES / 'ui_screenshots')
    if shutil.which('pdftoppm'):
        subprocess.run(['pdftoppm', '-scale-to', '1500', '-singlefile', '-png',
                        str(arch), str(arch.with_suffix(''))], check=True)
    print('Wrote architecture and UI evidence PDFs to', args.output_dir)


if __name__ == '__main__':
    main()
