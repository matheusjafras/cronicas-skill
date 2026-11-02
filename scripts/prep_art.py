"""Prepara as obras de um episódio lite e preenche "arts" no episode.json.

Uso: python prep_art.py <pasta_das_obras_originais> <projeto/public/lite/epNN_slug> <projeto/src/lite/epNN_slug/episode.json>

- reduz cada obra para no máximo 1800 px no lado maior (JPG 90): basta para a câmera do lite e pesa menos no render
- gera o fundo já desfocado em bg/ (~640 px, GaussianBlur 7): nada de blur() por quadro
- chave de cada obra = nome do arquivo sem extensão (minúsculas, sem acentos, "_")
- mantém title/meta já preenchidos; obras novas entram com title/meta vazios (preencha com os créditos)
"""
import glob
import json
import os
import re
import sys
import unicodedata

from PIL import Image, ImageFilter, ImageOps

Image.MAX_IMAGE_PIXELS = None
MAX = 1800
BG = 640
EXT = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")


def key(name):
    s = unicodedata.normalize("NFD", name.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def public_rel(out):
    # caminho de `out` relativo à pasta public/ do projeto (como o staticFile espera)
    parts = os.path.abspath(out).replace("\\", "/").split("/")
    return "/".join(parts[parts.index("public") + 1 :])


def main(src, out, ep_json):
    os.makedirs(os.path.join(out, "bg"), exist_ok=True)
    with open(ep_json, encoding="utf-8") as f:
        data = json.load(f)
    arts = data.setdefault("arts", {})
    rel = public_rel(out)
    for p in sorted(glob.glob(os.path.join(src, "*"))):
        if not p.lower().endswith(EXT):
            continue
        k = key(os.path.splitext(os.path.basename(p))[0])
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        orig = im.size
        scale = min(1.0, MAX / max(im.size))
        if scale < 1:
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        im.save(os.path.join(out, f"{k}.jpg"), quality=90, optimize=True)
        bg = im.copy()
        bg.thumbnail((BG, BG))
        bg.filter(ImageFilter.GaussianBlur(7)).save(os.path.join(out, "bg", f"{k}.jpg"), quality=80)
        prev = arts.get(k, {})
        arts[k] = {
            "file": f"{rel}/{k}.jpg",
            "bg": f"{rel}/bg/{k}.jpg",
            "w": im.width,
            "h": im.height,
            "title": prev.get("title", ""),
            "meta": prev.get("meta", ""),
        }
        warn = "  ← baixa resolução (peça/procure ≥ 1200 px)" if min(orig) < 900 else ""
        print(f"{k}: {orig[0]}×{orig[1]} → {im.width}×{im.height}{warn}")
    with open(ep_json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
