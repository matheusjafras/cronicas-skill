"""Junta os quadros renderizados por scripts/stills.mjs em folhas de contato para revisão visual.

Uso: python review_sheet.py <pasta_dos_quadros>   -> cria sheet1.jpg, sheet2.jpg... (6 quadros por folha)
"""
import glob
import os
import sys

from PIL import Image, ImageDraw

d = sys.argv[1]
for old in glob.glob(os.path.join(d, "sheet*.jpg")):
    os.remove(old)
fs = sorted(glob.glob(os.path.join(d, "f*.jpg")))
for k in range(0, len(fs), 6):
    chunk = fs[k : k + 6]
    sheet = Image.new("RGB", (3 * 400, 2 * 730), "white")
    draw = ImageDraw.Draw(sheet)
    for i, f in enumerate(chunk):
        x, y = (i % 3) * 400, (i // 3) * 730
        sheet.paste(Image.open(f).resize((400, 711)), (x, y + 18))
        draw.text((x + 4, y + 3), os.path.basename(f), fill="black")
    out = os.path.join(d, f"sheet{k // 6 + 1}.jpg")
    sheet.save(out, quality=85)
    print(out)
