"""Prepara as pinturas de um episódio para o Remotion.

Uso: python prepare_images.py <pasta_das_pinturas> <projeto/public/epNN>

- remove linhas/bordas claras nas laterais (sobras de recorte de grade)
- amplia com Lanczos + nitidez quando a imagem tiver menos de 1100 px na menor lateral
- salva como JPG (qualidade 93) com o mesmo nome base
Mostra o tamanho original de cada arquivo para avisar o usuário quando a resolução for baixa.
"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

TARGET = 1100


def trim_light_edges(im):
    a = np.asarray(im.convert("L")).astype(int)
    h, w = a.shape
    left, top, right, bottom = 0, 0, w, h
    while right - left > w * 0.8 and a[:, right - 1].mean() > 190:
        right -= 1
    while right - left > w * 0.8 and a[:, left].mean() > 190:
        left += 1
    while bottom - top > h * 0.8 and a[bottom - 1, :].mean() > 190:
        bottom -= 1
    while bottom - top > h * 0.8 and a[top, :].mean() > 190:
        top += 1
    # margem de segurança quando houve corte
    m = 2 if (left, top, right, bottom) != (0, 0, w, h) else 0
    return im.crop((left + m, top + m, right - m, bottom - m)), (w, h) != (right - left, bottom - top)


def main():
    src, out = sys.argv[1:3]
    os.makedirs(out, exist_ok=True)
    files = sorted(f for ext in ("png", "jpg", "jpeg", "webp") for f in glob.glob(os.path.join(src, f"*.{ext}")))
    low = []
    for f in files:
        im = Image.open(f).convert("RGB")
        orig = im.size
        im, trimmed = trim_light_edges(im)
        k = max(1, int(np.ceil(TARGET / min(im.size))))
        if k > 1:
            im = im.resize((im.width * k, im.height * k), Image.LANCZOS).filter(
                ImageFilter.UnsharpMask(radius=2.2, percent=90, threshold=2)
            )
            low.append(os.path.basename(f))
        name = os.path.splitext(os.path.basename(f))[0] + ".jpg"
        im.save(os.path.join(out, name), quality=93)
        print(f"{os.path.basename(f)}: {orig[0]}x{orig[1]} -> {im.width}x{im.height}{' (bordas removidas)' if trimmed else ''}{f' (ampliada {k}x)' if k > 1 else ''}")
    if low:
        print(f"\nATENÇÃO: {len(low)} imagem(ns) em baixa resolução foram ampliadas. Peça versões em alta (>= 1500 px) se possível.")


if __name__ == "__main__":
    main()
