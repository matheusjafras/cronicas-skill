"""Confere um episódio lite antes de abrir no Studio ou renderizar.

Uso: python check_lite.py <projeto/src/lite/epNN_slug>   (lê episode.json e words.json da pasta)

Faz a mesma busca do Remotion: cada âncora em sequência, cada frase `at` a partir da âncora do
seu bloco. Confere obras, arquivos e créditos, e mostra quanto dura cada bloco. Avisa blocos
longos (> 12 s: pouca coisa nova na tela) e curtos (< 2,5 s). Sai com código 1 se houver erro.
"""
import json
import os
import re
import sys
import unicodedata

FPS, OFFSET, TAIL = 30, 6, 4


def norm(w):
    w = unicodedata.normalize("NFD", w)
    w = "".join(c for c in w if not ("̀" <= c <= "ͯ")).lower()
    return re.sub(r"[^a-z0-9]", "", w)


def main(folder):
    with open(os.path.join(folder, "episode.json"), encoding="utf-8") as f:
        data = json.load(f)
    with open(os.path.join(folder, "words.json"), encoding="utf-8") as f:
        words = json.load(f)
    public = os.path.normpath(os.path.join(folder, "..", "..", "..", "public"))
    errors, warns = [], []
    gaps = sorted(data.get("pauses", []), key=lambda g: g["afterMs"])
    shift = lambda ms: sum(g["ms"] for g in gaps if ms >= g["afterMs"])
    starts_ms = [w["startMs"] + shift(w["startMs"]) for w in words]
    end_ms = words[-1]["endMs"] + shift(words[-1]["endMs"])
    tokens = [norm(w["text"]) for w in words]
    frame = lambda i: round(starts_ms[i] / 1000 * FPS) + OFFSET

    def index(phrase, after):
        p = [norm(t) for t in phrase.split()]
        for i in range(after, len(tokens) - len(p) + 1):
            if all(tokens[i + k] == t for k, t in enumerate(p)):
                return i
        return -1

    for name in ("voice", "music"):
        if data.get(name) and not os.path.isfile(os.path.join(public, data[name])):
            errors.append(f'{name}: arquivo não existe em public/: {data[name]}')
    for k, a in data.get("arts", {}).items():
        for fld in ("file", "bg"):
            if not os.path.isfile(os.path.join(public, a.get(fld, ""))):
                errors.append(f'obra "{k}": {fld} não existe: {a.get(fld)}')
        if not a.get("title") or not a.get("meta"):
            warns.append(f'obra "{k}": falta title/meta (crédito na tela)')

    blocks = data.get("blocks", [])
    idx, cursor = [], 0
    for n, b in enumerate(blocks, 1):
        i = index(b["anchor"], cursor)
        if i < 0:
            errors.append(f'bloco {n}: âncora não encontrada depois do bloco anterior: "{b["anchor"]}"')
            i = cursor
        idx.append(i)
        cursor = i + 1
        for key in ([b.get("art")] if b.get("art") else []):
            if key not in data.get("arts", {}):
                errors.append(f'bloco {n}: obra "{key}" não está em "arts"')
        cues = [c["at"] for c in b.get("highlights", []) + b.get("lines", []) + b.get("items", [])]
        for c in cues:
            if index(c, i) < 0:
                errors.append(f'bloco {n}: frase "{c}" não aparece depois da âncora "{b["anchor"]}"')
        if b["type"] == "list" and not 2 <= len(b["items"]) <= 4:
            errors.append(f"bloco {n}: lista precisa de 2 a 4 itens")
        if b["type"] in ("title", "end") and len(b["lines"]) > 4:
            warns.append(f"bloco {n}: mais de 4 linhas no centro")
        if b["type"] == "quote":
            parts = [p for p in b["text"].split() if norm(p)]
            toks = [norm(p) for p in parts]
            hit = any(all(tokens[s + j] == t for j, t in enumerate(toks)) for s in range(i, min(len(tokens) - len(toks), i + 80) + 1))
            if not hit:
                warns.append(f"bloco {n}: citação diferente da narração — as palavras entram em cascata, não no tempo da fala")

    total = round(end_ms / 1000 * FPS) + OFFSET + TAIL * FPS
    starts = [0 if n == 0 else frame(i) - 8 for n, i in enumerate(idx)]
    print(f'{data.get("id")}: {len(blocks)} blocos · {total / FPS:.1f} s')
    review = []
    for n, b in enumerate(blocks):
        dur = ((starts[n + 1] if n + 1 < len(blocks) else total) - starts[n]) / FPS
        review.append(starts[n] + round(dur * FPS * 0.75))
        flag = "  ← longo" if dur > 12 else "  ← curto" if dur < 2.5 else ""
        print(f"  {n + 1:02d} {b['type']:<6} {starts[n] / FPS:6.1f}s  {dur:4.1f}s  {b['anchor']}{flag}")
        if flag:
            warns.append(f"bloco {n + 1}: {dur:.1f} s{flag.replace('  ←', ' —')}")
    if total / FPS > 115:
        warns.append(f"duração {total / FPS:.0f} s passa de 1min50")
    # um quadro por bloco, perto do fim (quando tudo já apareceu), para scripts/stills.mjs
    print("quadros para revisão:", " ".join(str(f) for f in review))
    for w in warns:
        print("aviso:", w)
    for e in errors:
        print("ERRO:", e)
    print("ok" if not errors else f"{len(errors)} erro(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
