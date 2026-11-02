"""Tempo de cada palavra do texto oficial da narração (para legendas e sincronização de cenas).

Uso: python align_words.py <narracao.mp3> <narracao_oficial.txt> <saida words.json>

Transcreve com faster-whisper (timestamps por palavra), alinha ao texto oficial e, onde o
reconhecimento falhar (trechos sem tempo ou com tempos amontoados), retranscreve só aquele trecho.
Rode sem `python -I` (as bibliotecas estão instaladas com --user).
"""
import difflib
import json
import re
import sys
import unicodedata

import av
import numpy as np
from faster_whisper import WhisperModel

SR = 16000


def load_audio(path):
    # decodifica com PyAV (faster-whisper 1.2.1 é incompatível com PyAV 19 ao abrir arquivos)
    c = av.open(path)
    rs = av.AudioResampler(format="s16", layout="mono", rate=SR)
    pcm = np.concatenate([f.to_ndarray().reshape(-1) for fr in c.decode(audio=0) for f in rs.resample(fr)])
    c.close()
    return pcm.astype(np.float32) / 32768.0


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(ch for ch in w if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def transcribe(model, audio, offset=0.0):
    segs, _ = model.transcribe(audio, language="pt", word_timestamps=True, vad_filter=False)
    return [(w.word.strip(), w.start + offset, w.end + offset) for s in segs for w in s.words]


def align(script_words, hyp):
    a = [norm(w) for w in script_words]
    b = [norm(h[0]) for h in hyp]
    times = [None] * len(a)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = hyp[j1 + k][1:]
        elif tag == "replace":
            s, e = hyp[j1][1], hyp[j2 - 1][2]
            n = i2 - i1
            for k in range(n):
                times[i1 + k] = (s + (e - s) * k / n, s + (e - s) * (k + 1) / n)
    return times


def bad_runs(times, min_len=3):
    """Trechos sem tempo ou com várias palavras no mesmo instante."""
    runs, i = [], 0
    while i < len(times):
        j = i
        if times[i] is None:
            while j < len(times) and times[j] is None:
                j += 1
        else:
            while j + 1 < len(times) and times[j + 1] is not None and abs(times[j + 1][0] - times[i][0]) < 0.05:
                j += 1
            j += 1
            if j - i < min_len:
                i += 1
                continue
        runs.append((i, j))
        i = max(j, i + 1)
    return runs


def main():
    audio_path, script_path, out_path = sys.argv[1:4]
    script_words = open(script_path, encoding="utf-8").read().split()
    audio = load_audio(audio_path)
    dur = len(audio) / SR
    model = WhisperModel("small", device="cpu", compute_type="int8")

    times = align(script_words, transcribe(model, audio))

    for i, j in bad_runs(times):
        s = max(0.0, (times[i - 1][1] if i > 0 and times[i - 1] else 0) - 0.5)
        e = min(dur, (times[j][0] if j < len(times) and times[j] else dur) + 0.5)
        sub = align(script_words[i:j], transcribe(model, audio[int(s * SR) : int(e * SR)], offset=s))
        for k, t in enumerate(sub):
            if t:
                times[i + k] = t
        print(f"retranscrito: palavras {i}-{j} ({s:.1f}s-{e:.1f}s)")

    # preenche o que sobrou por interpolação
    for i in range(len(times)):
        if times[i] is None:
            prev = times[i - 1][1] if i > 0 else 0
            nxt = next((t[0] for t in times[i + 1 :] if t), prev + 0.3)
            times[i] = (prev, max(prev + 0.1, min(nxt, prev + 0.4)))

    remaining = len(bad_runs(times))
    caps = [
        {
            "text": (" " if i else "") + w,
            "startMs": round(t[0] * 1000),
            "endMs": round(t[1] * 1000),
            "timestampMs": round((t[0] + t[1]) * 500),
            "confidence": None,
        }
        for i, (w, t) in enumerate(zip(script_words, times))
    ]
    json.dump(caps, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"{len(caps)} palavras · áudio {dur:.1f}s · trechos ainda suspeitos: {remaining} · salvo em {out_path}")


if __name__ == "__main__":
    main()
