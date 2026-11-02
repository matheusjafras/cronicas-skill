"""Cria um episódio no formato lite ou regenera o registro dos episódios lite.

Uso:
  python new_lite.py <RAIZ> <nº> <slug_sem_acentos>   cria as pastas e o episode.json inicial
  python new_lite.py <RAIZ> --registry                 regenera projeto/src/lite/registry.ts

Um episódio só entra no registro (e no Studio) quando tem episode.json com blocos e words.json
com palavras; antes disso ele fica de fora, para não quebrar os outros.
"""
import json
import os
import sys


def comp_id(num, slug):
    return f"Ep{num:02d}-" + "-".join(p.capitalize() for p in slug.split("_") if p)


def registry(root):
    lite = os.path.join(root, "projeto", "src", "lite")
    entries = []
    for name in sorted(os.listdir(lite)):
        d = os.path.join(lite, name)
        ep, wd = os.path.join(d, "episode.json"), os.path.join(d, "words.json")
        if not (os.path.isfile(ep) and os.path.isfile(wd)):
            continue
        with open(ep, encoding="utf-8") as f:
            data = json.load(f)
        with open(wd, encoding="utf-8") as f:
            words = json.load(f)
        if not data.get("blocks") or not words:
            print(f"  fora do registro: {name} (faltam blocos ou narração)")
            continue
        entries.append(name)
    lines = [
        "// Gerado por .claude/skills/cronicas/scripts/new_lite.py --registry — não edite à mão.",
        'import type { Caption } from "@remotion/captions";',
        'import type { LiteData } from "./types";',
    ]
    for i, n in enumerate(entries):
        lines += [f'import d{i} from "./{n}/episode.json";', f'import w{i} from "./{n}/words.json";']
    lines += ["", "export const LITE: { slug: string; data: LiteData; words: Caption[] }[] = ["]
    lines += [f'  {{ slug: "{n}", data: d{i} as unknown as LiteData, words: w{i} as Caption[] }},' for i, n in enumerate(entries)]
    lines += ["];", ""]
    with open(os.path.join(lite, "registry.ts"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("registro:", ", ".join(entries) or "(vazio)")


def write_new(path, text):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)


def create(root, num, slug):
    folder = f"ep{num:02d}_{slug}"
    cr = os.path.join(root, "CRONICAS SAGRADAS", folder)
    os.makedirs(os.path.join(cr, "obras_originais"), exist_ok=True)
    write_new(os.path.join(cr, "narracao_oficial.txt"), "")
    write_new(
        os.path.join(cr, "creditos_e_fontes.md"),
        f"# Créditos e fontes — {folder}\n\n| Obra (chave) | Autoria | Data | Acervo | Licença | URL | Blocos |\n|---|---|---|---|---|---|---|\n",
    )
    os.makedirs(os.path.join(root, "projeto", "public", "lite", folder, "bg"), exist_ok=True)
    src = os.path.join(root, "projeto", "src", "lite", folder)
    os.makedirs(src, exist_ok=True)
    skeleton = {
        "id": comp_id(num, slug),
        "voice": f"voiceover/{folder}.mp3",
        "music": "audio/trilha_medieval.wav",
        "pauses": [],
        "arts": {},
        "blocks": [],
    }
    write_new(os.path.join(src, "episode.json"), json.dumps(skeleton, ensure_ascii=False, indent=2) + "\n")
    print("composição:", skeleton["id"])
    print("roteiro/créditos/obras originais:", cr)
    print("dados do episódio:", os.path.join(src, "episode.json"))
    print("obras prontas:", os.path.join(root, "projeto", "public", "lite", folder))
    registry(root)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) == 3 and sys.argv[2] == "--registry":
        registry(sys.argv[1])
    elif len(sys.argv) == 4:
        create(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    else:
        sys.exit(__doc__)
