"""Cria a estrutura de um novo episódio do Crônicas do Sagrado no projeto Remotion.

Uso: python new_episode.py <raiz "EDIÇÃO DE VIDEO"> <numero> <slug>
Ex.:  python new_episode.py . 2 pedro_nega_jesus

Cria:
  CRONICAS SAGRADAS/epNN_<slug>/   (pinturas, narracao_oficial.txt, storyboard)
  projeto/public/epNN/             (pinturas preparadas)
  projeto/src/epNN/timeline.ts     (tempo da narração, lê words.json)
  projeto/src/epNN/Scenes.tsx      (cenas — modelo com abertura e encerramento)
  projeto/src/epNN/EpisodeNN.tsx   (lista de cenas, efeitos e clima da trilha)
  e registra a composição "EpNN-<Slug>" em projeto/src/Root.tsx.
Não sobrescreve nada que já exista.
"""
import json
import os
import sys

root, num, slug = sys.argv[1], int(sys.argv[2]), sys.argv[3]
nn = f"{num:02d}"
ep = f"ep{nn}"
Comp = f"Episode{nn}"
comp_id = f"Ep{nn}-" + "-".join(p.capitalize() for p in slug.split("_"))[:40]
proj = os.path.join(root, "projeto")
src = os.path.join(proj, "src", ep)
docs = os.path.join(root, "CRONICAS SAGRADAS", f"{ep}_{slug}")


def write(path, text):
    if os.path.exists(path):
        print("já existe, mantido:", path)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("criado:", path)


os.makedirs(os.path.join(docs, "pinturas_originais"), exist_ok=True)
os.makedirs(os.path.join(proj, "public", ep), exist_ok=True)
write(os.path.join(docs, "narracao_oficial.txt"), "")
write(os.path.join(src, "words.json"), json.dumps([{"text": "…", "startMs": 0, "endMs": 1000, "timestampMs": 500, "confidence": None}]))

write(
    os.path.join(src, "timeline.ts"),
    f"""import type {{ Caption }} from "@remotion/captions";
import {{ createEpisodeTimeline }} from "../cronicas/Episode";
import wordsJson from "./words.json";

export const ep = createEpisodeTimeline(wordsJson as Caption[], {{ fps: 30, audioOffset: 6, tailSeconds: 3 }});
export const {{ tl, words }} = ep;
export const FPS = ep.fps;
export const TOTAL_FRAMES = ep.total;
""",
)

write(
    os.path.join(src, "Scenes.tsx"),
    f"""import React from "react";
import {{ AbsoluteFill, useCurrentFrame }} from "remotion";
import {{ Backdrop }} from "../cronicas/Backdrop";
import {{ Arch, BaroqueFrame, GothicWindow, Medallion, Painting, TornPaper }} from "../cronicas/Frames";
import {{ CoinsFall, Counter, LightSweep, Rewind, Rosette }} from "../cronicas/Graphics";
import {{ DrawIcon, IconBadge, IconRow }} from "../cronicas/Icons";
import {{ CameraShake, CheckItem, Connector, HandCircle, HandUnderline, LightLeak, LightRays, Parallax, Particles, PopWord, Spotlight, StrikeX, Typewriter }} from "../cronicas/Motion";
import {{ useSceneStart }} from "../cronicas/Scene";
import {{ BibleRef, HistoricTitle, Kicker, Note, OrnamentLine, Scroll, SignOff, WordsAt }} from "../cronicas/Type";
import {{ C, SERIF_TITLE, easeInOut, io }} from "../cronicas/theme";
import {{ tl }} from "./timeline";

// Pinturas do episódio (projeto/public/{ep}/). Preencha com os arquivos reais.
export const IMG: Record<string, string> = {{}};

const cx = (w: number) => (1080 - w) / 2;

// Quadro local (dentro da cena) em que uma frase começa a ser falada.
const useCue = () => {{
  const start = useSceneStart();
  return (phrase: string, after?: string) => tl.at(phrase, after) - start;
}};

// Modelo de cena: pintura em moldura barroca + título no tempo da fala.
export const S01Abertura: React.FC<{{ dur: number; img: string; title: string; titleAt: string }}> = ({{ dur, img, title, titleAt }}) => {{
  const frame = useCurrentFrame();
  const cue = useCue();
  const w = 740;
  return (
    <AbsoluteFill>
      <Backdrop tone="sepia" />
      <Kicker text="Crônicas do Sagrado" top={{262}} at={{0}} />
      <BaroqueFrame w={{w}} h={{840}} style={{{{ left: cx(w), top: 350, scale: String(io(frame, [0, 22], [0.9, 1])), opacity: io(frame, [0, 8], [0, 1]) }}}}>
        <Painting src={{img}} move={{{{ from: {{ s: 1.25 }}, to: {{ s: 1.08 }}, dur }}}} />
        <LightSweep at={{4}} dur={{50}} />
      </BaroqueFrame>
      <HistoricTitle text={{title}} top={{1240}} at={{cue(titleAt)}} size={{72}} color={{C.goldLight}} tracking={{8}} />
    </AbsoluteFill>
  );
}};

// Modelo de encerramento: arco com a pintura final, palavra-chave e assinatura do canal.
export const SFinal: React.FC<{{ dur: number; img: string; word: string; wordAt: string; narrationEnd: number }}> = ({{ dur, img, word, wordAt, narrationEnd }}) => {{
  const frame = useCurrentFrame();
  const cue = useCue();
  const logo = narrationEnd + 8;
  return (
    <AbsoluteFill>
      <Backdrop tone="light" glowY={{30}} />
      <AbsoluteFill style={{{{ opacity: io(frame, [logo, logo + 40], [1, 0]) }}}}>
        <Arch w={{820}} h={{920}} style={{{{ left: cx(820), top: 330 }}}}>
          <Painting src={{img}} move={{{{ from: {{ s: 1.1 }}, to: {{ s: 1.0 }}, dur }}}} />
        </Arch>
        <HistoricTitle text={{word}} top={{220}} at={{cue(wordAt)}} size={{72}} color={{C.wine}} tracking={{12}} />
      </AbsoluteFill>
      <SignOff at={{logo}} />
    </AbsoluteFill>
  );
}};

// Evita avisos de import não usado enquanto as cenas são escritas.
export const _kit = {{ Arch, GothicWindow, Medallion, TornPaper, CoinsFall, Counter, Rewind, Rosette, BibleRef, Note, OrnamentLine, Scroll, WordsAt, SERIF_TITLE, easeInOut, DrawIcon, IconBadge, IconRow, CameraShake, CheckItem, Connector, HandCircle, HandUnderline, LightLeak, LightRays, Parallax, Particles, PopWord, Spotlight, StrikeX, Typewriter }};
""",
)

write(
    os.path.join(src, f"{Comp}.tsx"),
    f"""import React from "react";
import {{ EpisodeComposition, MoodCue, SceneDef, SfxDef }} from "../cronicas/Episode";
import * as S from "./Scenes";
import {{ ep, tl }} from "./timeline";

// Cada cena abre na frase da narração indicada em "anchor" (texto exato, sem pontuação obrigatória).
const SCENES: SceneDef[] = [
  // {{ name: "01 Abertura", anchor: "primeiras palavras", enter: "fade", render: (d) => <S.S01Abertura dur={{d}} img={{S.IMG.x}} title="TÍTULO" titleAt="palavra" /> }},
];

const SFX: SfxDef[] = [
  // {{ src: "audio/moedas.wav", at: tl.at("frase"), volume: 0.4 }},
];

const MOODS: MoodCue[] = [{{ from: 0, mood: "dark" }}];

export const {Comp}: React.FC = () => (
  <EpisodeComposition ep={{ep}} scenes={{SCENES}} voiceover="voiceover/{ep}_{slug}.mp3" moods={{MOODS}} sfx={{SFX}} />
);

void tl;
void S;
""",
)

# Registro no Root.tsx
root_tsx = os.path.join(proj, "src", "Root.tsx")
s = open(root_tsx, encoding="utf-8").read()
if f'id="{comp_id}"' in s:
    print("composição já registrada:", comp_id)
else:
    imp = f'import {{ {Comp} }} from "./{ep}/{Comp}";\nimport {{ TOTAL_FRAMES as {ep.upper()}_FRAMES }} from "./{ep}/timeline";\n'
    s = s.replace('import { Composition, Folder } from "remotion";\n', 'import { Composition, Folder } from "remotion";\n' + imp, 1)
    reg = f"""      <Folder name="Cronicas-do-Sagrado">
        <Composition
          id="{comp_id}"
          component={{{Comp}}}
          durationInFrames={{{ep.upper()}_FRAMES}}
          fps={{30}}
          width={{1080}}
          height={{1920}}
        />"""
    s = s.replace('      <Folder name="Cronicas-do-Sagrado">', reg, 1)
    open(root_tsx, "w", encoding="utf-8").write(s)
    print("registrado no Root.tsx:", comp_id)
print(json.dumps({"episode": ep, "composition": comp_id, "voiceover": f"public/voiceover/{ep}_{slug}.mp3"}, ensure_ascii=False))
