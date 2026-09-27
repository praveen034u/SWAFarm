"""Render generated manufacturing outputs for final visual QA; never edit designs."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '2026-09-21/tool-deps'))
import fitz

base = Path(__file__).resolve().parent
out = base / 'release-candidate'
sheet = fitz.open()
page = sheet.new_page(width=1600, height=1500)
for i, path in enumerate(sorted((out / 'review/independent').glob('*.svg'))):
    x, y = (i % 4) * 400, (i // 4) * 375
    page.insert_text((x+12, y+20), path.stem, fontsize=10)
    source = fitz.open(path)
    pdf = fitz.open('pdf', source.convert_to_pdf())
    page.show_pdf_page(fitz.Rect(x+8, y+30, x+392, y+360), pdf, 0)
page.get_pixmap().save(base / 'reports/layer-contact-sheet.png')
for side in ('top', 'bottom'):
    doc = fitz.open(out / f'assembly/assembly-{side}.pdf')
    doc[0].get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(base / f'reports/final-assembly-{side}.png')
doc=fitz.open(out / 'assembly/schematic.pdf')
print('Schematic pages:', len(doc))
print('Independent layers:', len(list((out/'review/independent').glob('*.svg'))))
