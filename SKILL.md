---
name: cronicas
description: Produz episódios do canal católico "Crônicas do Sagrado" no template Remotion — do roteiro e pinturas até o MP4 final e o vídeo agendado no Instagram, no TikTok e no YouTube Shorts, etapa por etapa (novo episódio, imagens, storyboard, narração ElevenLabs, montagem, revisão, render, publicação agendada via Zernio + API do YouTube, ajustes). Tem também o modo leve `/cronicas lite`: lotes de vários episódios (Claude escreve os roteiros e acha as obras) montados por dados, com render rápido e fila. Use quando o usuário digitar /cronicas ou /cronicas lite, pedir episódios em volume/em lote/mais leves, pedir um novo episódio, pedir para agendar/postar um episódio no Instagram, no TikTok ou no YouTube, ou pedir para refazer uma etapa de um episódio existente.
---

# Crônicas do Sagrado — produção de episódio

Raiz: `C:\Users\user\OneDrive\Área de Trabalho\EDIÇÃO DE VIDEO` (abaixo, `RAIZ`).
Projeto Remotion: `RAIZ/projeto` · componentes reutilizáveis: `projeto/src/cronicas/` · guia: `projeto/CRONICAS.md`.
Episódio de referência (o padrão de qualidade): `projeto/src/ep01/` e `CRONICAS SAGRADAS/cronicas_do_sagrado_ep01_judas/storyboard_ep01.md`.
Documentos de cada episódio (narração, storyboard, legendas, créditos): `RAIZ/CRONICAS SAGRADAS/<pasta do episódio>/`.
O nome tem espaço: nos comandos, ponha o caminho entre aspas.
Scripts desta skill: `RAIZ/.claude/skills/cronicas/scripts/`.

Fale com o usuário em português do Brasil, com frases curtas. Ele prefere que o trabalho ande sozinho;
quando ele disser "não me pergunte mais nada / gere pra mim", siga até o fim sem parar.

## Como chamar

`/cronicas <etapa> [argumentos]`. Sem etapa, rode o **fluxo completo** (1→8), mostrando em que etapa está.

| Etapa | O que faz |
|---|---|
| `novo <nº> <slug>` | 1. cria a estrutura do episódio |
| `imagens` | 2. prepara as pinturas recebidas |
| `storyboard` | 3. lê narração + pinturas e escreve o storyboard |
| `narracao` | 4. gera a voz no ElevenLabs, baixa e marca o tempo de cada palavra |
| `montar` | 5. escreve as cenas no Remotion presas às frases |
| `revisar` | 6. renderiza quadros-chave, olha e corrige |
| `render` | 7. renderiza o MP4 final e entrega |
| `publicar [data/hora]` | 8. escreve a legenda e **agenda** o vídeo no Instagram e no TikTok (Zernio) e no YouTube Shorts (API) |
| `trocar-imagens` | substitui pinturas (ex.: versões em alta) e renderiza de novo |
| `ajustar <pedido>` | muda uma cena/tempo/texto pedida pelo usuário, revisa e renderiza |
| `lite [N ou temas]` | **formato leve, em lote** (padrão: 3 episódios): leia e siga **`LITE.md`** desta pasta |

Descubra o episódio em andamento pela pasta `projeto/src/epNN` mais recente, se o usuário não disser.

---

## 1. Novo episódio

```bash
cd "RAIZ" && python .claude/skills/cronicas/scripts/new_episode.py . <nº> <slug_sem_acentos>
```
Cria `CRONICAS SAGRADAS/epNN_<slug>/` (com `pinturas_originais/` e `narracao_oficial.txt`), `projeto/public/epNN/`,
`projeto/src/epNN/{timeline.ts, Scenes.tsx, EpisodeNN.tsx, words.json}` e registra a composição no `Root.tsx`.
Salve o texto da narração **exatamente como o usuário enviou** em `narracao_oficial.txt` (sem `**`, sem tags).
Se o usuário mandou um ZIP/pasta de pinturas, copie para `pinturas_originais/` e leia `manifesto_cenas.json`/`LEIA_ME.txt` se existirem.

## 2. Imagens

```bash
python .claude/skills/cronicas/scripts/prepare_images.py "CRONICAS SAGRADAS/epNN_<slug>/pinturas_originais" "projeto/public/epNN"
```
Remove bordas claras de recorte e amplia imagens pequenas. Se avisar baixa resolução, diga ao usuário
(peça versões ≥ 1500 px, uma por arquivo, não em grade), mas continue com as ampliadas.
Olhe todas as pinturas (monte uma folha de contato com PIL e use Read) antes do storyboard.
Preencha `IMG` em `projeto/src/epNN/Scenes.tsx` com os caminhos `epNN/<arquivo>.jpg`.

**Obras históricas reais (desde o Ep. 04 — nada de IA):** o usuário manda um pacote com manifesto + `baixar_imagens.py`
(as obras vêm de museus: Met, Cleveland, Wikimedia). Rode o script; se o Wikimedia der HTTP 429, baixe pelo endereço direto
`upload.wikimedia.org/wikipedia/commons/<md5[0]>/<md5[:2]>/<arquivo>`. Depois do `prepare_images.py`, reduza para no máximo
2400 px e gere fundos já desfocados em `public/epNN/bg/` (PIL, ~640 px, GaussianBlur 7) — nada de `blur()` CSS por quadro.
As obras têm proporções variadas: **sempre passe `img={{w, h}}` ao `Cam`/`DepthPainting`** (sem isso a câmera assume 9:16 e
distorce). Modelo: registro `ART` em `src/ep04/Scenes.tsx` (arquivo, tamanho, título, artista · data · acervo) + `ArtLabel`
na tela. Mantenha `CRONICAS SAGRADAS/epNN_<slug>/creditos_e_fontes.md` (obra, autoria, data, acervo, licença, URL, cenas). Recortes,
molduras e figuras são tratamento editorial: nunca desenhe por cima da obra como se fosse parte dela; não remova marcas d'água;
crédito obrigatório em fotos CC BY (ex.: Bento XVI, Peter Nguyen, CC BY 2.0). Falta uma obra? Sinalize, não substitua por IA.

## 3. Storyboard

Escreva `CRONICAS SAGRADAS/epNN_<slug>/storyboard_epNN.md` no formato do Ep. 01: arco de cor por ato, tabela de cenas
(trecho exato · arquivo · composição · animação · texto editorial · som · transição) e tabela de uso das pinturas.
Antes do áudio, a duração é só estimativa (~2,3 palavras/s); os tempos reais vêm do `words.json`.

**Fidelidade teológica (obrigatório):** confira cada afirmação da narração com a Bíblia/Catecismo, cite as
referências no formato brasileiro (Jo 12,6 · Mt 26,14-16). Não invente fatos, não apresente hipótese como
verdade, não afirme o destino eterno de ninguém. Se algo estiver errado na narração, avise o usuário — não reescreva.

## 4. Narração (ElevenLabs — gasta créditos)

Peça autorização antes de gerar, a menos que o usuário já tenha dito para seguir. Conta do usuário é paga.
Antes de gerar, rode `estimate_only: true` e diga o custo (≈1 crédito por caractere no eleven_v4). Se o usuário mudar poucas
palavras depois, regrave só a frase e emende nas pausas (`silencedetect` + `atrim`/`concat`) — não a narração inteira.
Pausas extras (ex.: antes de uma revelação) entram no Remotion com `gaps` em `createEpisodeTimeline`, sem gerar de novo.
1. `creative_generate_speech` com `voice_id` **`sJfod1k0iiI5CA9IP0R2`** (Johnes Bittar – Gentle, Warm, PT-BR),
   `model_id` `eleven_v4`, `generations_count` 1, `prompt` = texto oficial com poucas tags de interpretação
   em inglês nas mudanças de tom (`[curious]`, `[calmly]`, `[seriously]`, `[pause]`, `[dramatically]`, `[softly]`,
   `[sadly]`, `[warmly]`). Tags não são faladas; o texto continua idêntico.
   Se a voz falhar, use outra voz brasileira masculina de narração (`creative_list_voices`, languages `pt`, accent `brazilian`).
2. `creative_get_flow_run_status` até `all_completed`; baixe `content_url` com `curl -sS -o projeto/public/voiceover/epNN_<slug>.mp3 "<url>"` (o link expira em 2 h).
3. Tempo das palavras (≈2–4 min, rode em segundo plano):
```bash
python .claude/skills/cronicas/scripts/align_words.py projeto/public/voiceover/epNN_<slug>.mp3 "CRONICAS SAGRADAS/epNN_<slug>/narracao_oficial.txt" projeto/src/epNN/words.json
```
Confira a saída: "trechos ainda suspeitos: 0". Se houver, abra o JSON e corrija aquele trecho.

## 5. Montagem

- **Legendas pequenas, sem cartela** (pedido do usuário no Ep. 03): passe `captions="plain"` ao `EpisodeComposition` (Inter 38 px, sombra escura, palavras-chave em dourado, y≈1532). Todo texto editorial das cenas fica acima de y≈1510.
- `EpisodeNN.tsx`: lista `SCENES` (`name`, `anchor` = primeiras palavras exatas da frase que abre a cena,
  `enter`/`exit` = transições da tabela em "Motion design", `render`), `SFX` (`tl.at("frase")`) e `MOODS` (trilha `dark`/`light`).
- `Scenes.tsx`: uma função por cena. Dentro dela, `cue("frase")` dá o quadro local em que a frase é falada;
  `cue("frase", "frase anterior")` desambigua repetições. Use `dur` para movimentos que duram a cena toda.
- Copie padrões do `ep01/Scenes.tsx` e varie. Kit disponível:
  - Molduras: `BaroqueFrame` (gold/wood), `Arch` (light/dark), `GothicWindow`, `Medallion`, `TornPaper`
  - Câmera: `Painting` com `move={{from:{s,x,y}, to:{s,x,y}, dur, delay, origin}}`
  - Texto: `Kicker`, `HistoricTitle`, `WordsAt`, `BibleRef`, `Scroll`, `OrnamentLine`, `Note`, `SignOff`
  - Gráficos: `CoinsFall`, `LightSweep`, `Rewind`, `Counter`, `Rosette`; fundos `Backdrop` por emoção
  - Áudio pronto em `public/audio/`: `moedas`, `moeda`, `papel`, `sino`, `impacto`, `sopro`, `trilha_escura`, `trilha_luz`
    (gerados por `projeto/scripts/synth_audio.py`, livres de direitos). Não use música de terceiros.
  - **Trilha musical (desde o Ep. 03):** o usuário quer música de fundo **medieval instrumental**. Gere com
    `python scripts/synth_medieval.py public/audio/trilha_<ep>.wav` (original, livre de direitos: harpa, bordão, flauta doce,
    tambor, órgão no clímax; ajuste FORM/melodias ao arco do roteiro) e passe `music={{ src, volume: 0.26, duck: 0.55 }}` ao
    `EpisodeComposition` (abaixa sob a voz, ~14 dB abaixo; sobe nas pausas).
- **Regras de direção de arte** (do usuário): nunca pintura "seca" em tela cheia; alternar composições
  (moldura, arco, janela, medalhão, papel rasgado, painel duplo, colagem com pergaminho); a mesma pintura pode
  voltar com outro enquadramento; fundo muda com a emoção (preto sépia/dourado → pergaminho → vinho → contraste
  → verde → luz); texto editorial curto, sem poluir; animação só quando comunica algo; final contemplativo + `SignOff`.
- **Motion design é obrigatório** — veja a seção "Motion design" abaixo. O Ep. 01 ficou com pouco motion;
  o usuário quer cara de After Effects: ícones que se desenham, anotações feitas na hora, câmera viva e transições com zoom.
- **Zonas da tela (1080×1920):** títulos 210–450 · pintura 330–1290 · legendas 1330–1480 (automáticas) ·
  nada importante abaixo de 1520 nem acima de 200.
- Valide: `cd projeto && npx tsc --noEmit`.

## Motion design (padrão "After Effects")

Catálogo vivo: composição **`Cronicas-Kit`** no Studio (`src/cronicas/KitDemo.tsx`) — mostra cada efeito funcionando;
copie de lá. Componentes em `src/cronicas/Icons.tsx`, `Motion.tsx`, `Scene.tsx` e (desde o Ep. 02) `Draw.tsx`,
`Kinetic.tsx`, `Diagrams.tsx`, `Camera.tsx`. O Ep. 02 (`src/ep02/Scenes.tsx`) é a referência de "motion graphics de verdade".

**Anti-slideshow (lição do Ep. 01):** a moldura **se desenha** antes da pintura aparecer por **máscara**; toda explicação
vira **diagrama** (linha do tempo, mapa, tabela, mapeamento I→I); texto é **cinético** (letras por máscara, palavras que se
transformam); transições **ligam ideias** (a chama vira máscara, a linha dourada vira horizonte e linha do tempo).
Pintura parada numa moldura pronta só em momento emocional, e no máximo 2–3 vezes por vídeo.

**Regras de densidade (cheque cena por cena):**
1. Algo novo se move a cada **2–3 s** de narração (ícone, anotação, palavra, câmera, luz). Nada parado > 3 s.
2. Toda cena tem **pelo menos 3 camadas animadas**: fundo/atmosfera + pintura com câmera + um elemento gráfico.
3. Todo **conceito-chave** falado ganha um ícone ou anotação no momento exato da palavra (`cue`).
4. Todo **detalhe de pintura** citado (mão, moeda, rosto) ganha `Spotlight` + `HandCircle` (+ `Connector` até o rótulo).
5. **Comparações** (X × Y, antes/depois, certo/errado) usam `IconBadge` lado a lado + `Connector`, ou `CheckItem`.
6. **Listas/passos** usam `IconRow` (ícones ligados por linha que se desenha).
7. **Impactos** (revelação, traição, "ninguém") = `PopWord` + `CameraShake` + som `impacto`.
8. Cenas escuras levam `Particles` (brasas/poeira); cenas de graça/luz levam `LightRays` e `LightLeak`.
9. Citações e documentos usam `Typewriter`; números usam `Counter`.
10. Nunca repita a mesma combinação (entrada + composição + efeito) em cenas seguidas.

**Kit de motion:**
| Componente | Para quê |
|---|---|
| `DrawIcon name size at` | ícone que se desenha traço a traço |
| `IconBadge name at x y label tone` | selo com anel desenhado, mola, pulso de luz e legenda |
| `IconRow items y` | 2–4 ícones em sequência ligados por linha |
| `HandCircle x y w h at` · `HandUnderline` · `StrikeX` | anotações feitas "à caneta" |
| `Connector from to at bend` | seta curva que se desenha entre dois pontos |
| `Spotlight from to at radius until` | escurece tudo e guia o olhar até um detalhe |
| `PopWord text at top` | palavra que estoura com mola e brilho |
| `Typewriter text at top` | máquina de escrever (citações) |
| `CheckItem text ok at top` | ✓ / ✗ animado (verdade × mito) |
| `CameraShake at` (envolve a cena) | tremor de impacto |
| `Parallax dur layers` | camadas em profundidade com velocidades diferentes |
| `Particles` · `LightRays` · `LightLeak` | atmosfera: poeira/brasas, raios divinos, vazamento de luz |
| **Construção (`Draw.tsx`)** | |
| `DrawnArch` · `DrawnFrame` · `DrawnOval` (`at dur tone reveal revealAt origin`) | arco/moldura/medalhão que se desenham, ganham massa e revelam a pintura por máscara (`up`, `down`, `left`, `radial`, `fade`) |
| `DrawCross cx cy size at dur` | cruz trevolada construída: guias, contorno pelos dois lados, botões, ouro e brilho com raios |
| `RomanNumeral n cx cy height at tone` | I, II, III construídos traço a traço (haste serifada + preenchimento + pulso) |
| `Flourish` · `OliveBranch` | divisor barroco simétrico; ramo de oliveira que brota |
| `Flame` · `Brazier` · `PathComet` | chama procedural viva; braseiro vetorial em primeiro plano; luz que corre num traço |
| **Câmera (`Camera.tsx`)** | |
| `Cam src w h keys` + `camState`/`camPoint` | câmera por quadros-chave {f, x, y, s} sobre a pintura; `camPoint` dá a posição na tela de um detalhe para ancorar círculos e setas |
| **Tipografia cinética (`Kinetic.tsx`)** | |
| `LetterReveal text at top` | letras que sobem de uma máscara, em cascata |
| `DepthWords words top` | palavras que chegam da profundidade (escala + desfoque) |
| `MorphWord from to at` | palavra que se desmonta e vira outra (AMOR → ATITUDES, DIZEMOS → VIVEMOS) |
| `QuoteReveal words` · `StrikeLine` · `Highlight` | citação palavra a palavra; risco à mão; marca-texto |
| **Diagramas (`Diagrams.tsx`)** | |
| `Timeline y nodes marker` | linha do tempo bíblica com marcador que avança ou rebobina |
| `Link from to at bend dashed glow` | ligação curva desenhada (seta, tracejado, brilho, desbotar) |
| `Cartouche` · `ConceptChain` · `CompassCircle` · `Pin` · `SourceTag` | cartela; A → B → C com selos; círculo a compasso; marca no mapa; fonte que entra pela lateral |
| `FlameReveal` · `ArchTunnel` · `PageTurn` | chama que vira máscara; túnel de arcos em profundidade; página que vira em 3D |
| **Ep. 03 (`Fire`, `Book`, `Manuscript`, `Architecture`, `Morph`, `Theology`)** | |
| `PaintedFire` · `Burn` · `TrialByFire` | fogo com cara de óleo; consumir um elemento até a cinza; prova dos materiais (1Cor 3,12) |
| `Codex` · `GhostWord` · `DrawnQuestion` · `Manicule` | Bíblia que vira páginas; palavra pontilhada ("não está escrito"); "?" a pena; ☞ dos copistas |
| `Parchment` · `InkText` · `DropCap` · `UnrollScroll` | folha com borda irregular; texto que aparece como tinta; capitular iluminada; rolo com cilindros |
| `Aedicula` · `CelestialGate` | moldura renascentista que se constrói; colunata em perspectiva com portas que abrem |
| `ShapeMorph` + `flameShape`/`mandorlaShape`/`archShape`/`rectShape` | uma forma vira outra (chama → mandorla; dois painéis → um arco) |
| `EraRibbon` · `VennParadox` · `CanonShelf` · `FoundationArch` · `PathOfGrace` · `InkStains` | fita de eras com câmera; dois conceitos que coexistem; estante do cânon; fundamentos + pedra-chave; caminho com portal; manchas que a luz levanta |
| `Inscription` · `HeatText` · `DepthPainting` | letras cinzeladas; tinta → brasa → ouro; pintura em 2.5D (personagem descolado do fundo) |
| **Ep. 04 (`Sacred.tsx`) — arte sacra histórica** | |
| `ArtLabel` | etiqueta de museu (obra · artista · data · acervo) que entra por máscara |
| `Chasm` (+ `attempts`: `voice`/`sight`/`cross`) | dois recortes que se separam por um abismo; voz e olhar atravessam, a linha de ouro para na borda com ✗ |
| `WaterDrop` | gota vetorial que se forma, cai e vira vapor antes de chegar |
| `StrokeFigure` · `FigureRow` | figuras de manto desenhadas a traço; fileira com numerais (os cinco irmãos) |
| `CrowdSplit` | grade de pessoas que uma linha divide em dois destinos |
| `EtymWord` | termo em língua original (grego/hebraico rtl/latim) escrito por máscara + transliteração + glosa (`HEBREW` em theme.ts) |
| `SmokeWisp` · `LifeLine` | fumaça vetorial (vela apagada); linha da vida → † → marco "depois da morte" |

Ícones disponíveis (`ICONS`): cruz, moeda, moedas, bolsa, biblia, pergaminho, coroa, coracao, olho, corrente,
balanca, chama, lagrima, calice, igreja, ampulheta, lua, sol, pessoa, pessoas, voltar, check, xis, pomba, chave, mapa, peixe, pao, ovelha, cajado, barco, livro,
vela, passos, coluna, braseiro, amizade.
Faltou um? Desenhe no mesmo estilo (traço, grade 24×24, 2–5 subcaminhos) e acrescente em `Icons.tsx`.

**Transições (`enter` / `exit` em cada cena de `SCENES`):**
| Uso | Saída da cena anterior → entrada da próxima |
|---|---|
| Mergulho em detalhe / "vamos voltar no tempo" | `exit: "zoomThrough"` → `enter: "zoomIn"` |
| Comparação, contraste, virada de lado | `exit: "whip"` → `enter: "whip"` |
| Ênfase seca / pergunta | `enter: "punch"` |
| Revelação, abertura de cenário | `enter: "zoomOut"` |
| Revelação divina, graça | `enter: "flash"` |
| Momento contemplativo, pausa | `exit: "blur"` → `enter: "blur"` |
| Entrar em outro lugar / pintura nova | `exit: "hold"` → `enter: "arch"` (portal em arco) |
| Fogo como elo entre ideias | `exit: "hold"` → `enter: "flame"` (ou `FlameReveal` dentro da cena) |
| A linha vira o próximo elemento (linha do tempo, horizonte) | `exit: "hold"` → `enter: "goldLine"` |
| Documento, citação, fonte | `exit: "hold"` → `enter: "scroll"` |
| Neutras (use pouco) | `fade`, `iris`, `wipe`, `rise`, `zoom` |
Entradas por máscara (`arch`, `flame`, `goldLine`, `scroll`) pedem `overlap: 22` (scroll: 24) na cena e `exit: "hold"` na anterior.
Varie: no máximo 2 transições iguais seguidas; pelo menos 1/3 das cenas com zoom (`zoomThrough`/`zoomIn`/`zoomOut`/`punch`).
Coloque um som (`sopro`, `impacto`, `papel`) em toda transição forte.

## 6. Revisão (obrigatória — o código pronto não é o fim)

```bash
cd projeto && node scripts/stills.mjs EpNN-<Slug> out/stills <quadro> <quadro> ...
python ../.claude/skills/cronicas/scripts/review_sheet.py out/stills
```
Escolha 1–2 quadros por cena (perto do fim de cada uma, quando tudo já apareceu) + o último quadro.
Inclua também 2–3 quadros no **meio de transições** e de animações de ícone, para ver o movimento.
Abra as folhas com Read e procure: cena com pouco movimento (aplique as regras de densidade), texto sobre a pintura ou a legenda, palavras quebradas/cortadas,
enquadramento ruim (rostos cortados), elementos parados no ar, cenas vazias, repetição de composição.
Corrija e renderize de novo só os quadros afetados.

## 7. Render e entrega

```bash
cd projeto && npx remotion render EpNN-<Slug> out/cronicas_epNN_<slug>.mp4 --codec=h264 --crf=18 --audio-codec=aac --concurrency=4 --gl=angle --x264-preset=veryfast
```
**Render rápido (desde o Ep. 04):** passe `fast` ao `EpisodeComposition` (papel, grão e fibras de pergaminho vêm de
`public/textures/*.png` em vez de `feTurbulence` a cada quadro), use os fundos pré-desfocados e imagens ≤ 2400 px. `--gl=angle` (GPU) renderiza ~2× mais rápido com imagem idêntica
(testado no Ep. 04). Nunca pare o terminal de um render em andamento: o FFmpeg cai na codificação (0xC0000142).
Rode em segundo plano (~10–20 min). Depois: confira com ffprobe (1080×1920, 30 fps, h264+aac, duração ≈ áudio + 3 s),
copie para `RAIZ/entregas/`, extraia 4–5 quadros do MP4 para conferir, e envie com `SendUserFile`. Depois, etapa 8.

## 8. Publicação no Instagram, no TikTok e no YouTube (sempre agendada)

Conector Zernio (ferramentas `mcp__c3fe37fd-…__*`; as que não aparecem na lista: `search_tools` + `call_tool`).
Um post só, com as duas contas, sai no mesmo horário nas duas redes. `profile_id` `6ae6755731c8c700fc50d6d4`.
| Rede | Conta | `accountId` |
|---|---|---|
| Instagram | @sagradocronicas | `6ae6772c8c2f0842d5864b8e` |
| TikTok | @cronicasdosagrado | `6ae67cbc9b6a21700a5cbc58` |

**Nunca publique na hora** (`publish_now`): o usuário quer os posts **agendados**. Só publique na hora se ele pedir com essas palavras.

1. **Contas:** `accounts_get_all_accounts_health`. Se alguma tiver `needsReconnect` ou `canPost: false`, pare e peça
   para reconectar em zernio.com (o token do Instagram vence em 30/12/2026; o do TikTok é renovado pelo Zernio a cada 24 h).
2. **Legenda** em `CRONICAS SAGRADAS/<pasta do episódio>/legenda_instagram.txt`, tirada da narração oficial (modelo: Ep. 01):
   - 1ª linha = o gancho do vídeo, até 125 caracteres (é o que aparece antes do "… mais");
   - corpo curto com frases da narração + referências bíblicas (Mt 27,3-5) — mesmas regras de fidelidade da etapa 3;
   - fecho `Crônicas do Sagrado · Ep.NN` + **um** pedido só (ex.: seguir para ver o próximo episódio);
   - no máximo **5 hashtags**, no fim; sem travessão.
3. **Upload do MP4** (não publica nada):
   `call_tool` `media_get_media_presigned_url` {`filename`, `content_type` `video/mp4`, `size`} → então
```bash
curl -sS -X PUT -H "Content-Type: video/mp4" --upload-file "entregas/cronicas_epNN_<slug>.mp4" -o /dev/null -w "HTTP %{http_code}\n" "<uploadUrl>"
```
   Espere `HTTP 200` (~1 min para 65 MB) e use o `publicUrl`. O link de upload vale 1 h; a mídia fica 7 dias — agende dentro disso ou reenvie.
4. **Validação:** `validate_media` (`publicUrl`; Instagram até 300 MB, TikTok até 10 min) e `validate_post` com
   `platforms: [{platform: "instagram", platformSpecificData: {contentType: "reels", shareToFeed: true}}, {platform: "tiktok"}]`.
   Corrija até "No validation issues found". Para o TikTok, rode também o passo 7 com `dry_run: true`
   (não cria nada; espere `canPublish: true`).
5. **Horário:** fila padrão **"Crônicas do Sagrado"** (`6ae68218b5bcae1b725392f5`): **1 vídeo por dia, todo dia, às 19h30**
   (`America/Sao_Paulo`; ritmo escolhido pelo usuário em 31/10/2026). Mostre o próximo horário livre com
   `queue_get_next_queue_slot` (ou vários com `queue_preview_queue`). Para mudar os horários: `queue_list_queue_slots` (`all: "true"`)
   e atualize a fila. Se o usuário der uma data, use-a.
6. **Aprovação:** mostre a legenda (bloco de código) + o horário e espere o "sim". Se ele já disse para seguir sem perguntas,
   agende e avise o horário e que dá para cancelar antes.
7. **Agendar** com `call_tool` `posts_create_post`:
```
content: <legenda>
media_items: [{type: "video", url: <publicUrl>, mimeType: "video/mp4"}]
platforms: [{platform: "instagram", accountId: "6ae6772c8c2f0842d5864b8e",
             platformSpecificData: {contentType: "reels", shareToFeed: true}},
            {platform: "tiktok", accountId: "6ae67cbc9b6a21700a5cbc58"}]
tiktok_settings: {privacyLevel: "PUBLIC_TO_EVERYONE", allowComment: true, allowDuet: false, allowStitch: false,
                  commercialContentType: "none", videoMadeWithAi: false,
                  contentPreviewConfirmed: true, expressConsentGiven: true}
queued_from_profile: "6ae6755731c8c700fc50d6d4"      ← próximo horário da fila
  (ou, para data escolhida: scheduled_for: "AAAA-MM-DDTHH:MM", timezone: "America/Sao_Paulo")
```
   - `contentPreviewConfirmed`/`expressConsentGiven` = o "sim" do usuário no passo 6 (exigência do TikTok): só mande `true` depois dele.
   - **Sem rótulo de IA:** `videoMadeWithAi: false` sempre. Decisão firme do usuário (31/10/2026); não ligue e não volte a sugerir.
     A API do Instagram não tem esse rótulo.
   - Privacidade: a conta só oferece `PUBLIC_TO_EVERYONE` (`accounts_get_tik_tok_creator_info`).
   Não use o atalho `posts_create` (não tem fila nem dados de Reel/TikTok) e não copie o horário de `queue_get_next_queue_slot`
   para `scheduled_for` (fura a trava da fila).
8. **Conferir:** `posts_get` → status `scheduled` e o horário certo; informe o ID ao usuário. Cancelar antes do horário:
   `posts_delete`. Depois do horário: `posts_list_failed` mostra falhas e `posts_retry` tenta de novo.

### YouTube Shorts (API oficial, grátis; não passa pelo Zernio)

O plano grátis do Zernio só cobre 2 contas, então o YouTube vai pelo script `scripts/youtube_upload.py`.
Canal **Crônicas do Sagrado** (`UCCaEJ0t4dUpsBSNKcb6GXsw`), conta Google `akicesagamestuto@gmail.com`.
As chaves ficam em `%USERPROFILE%\.cronicas-youtube\` (fora do OneDrive e do GitHub). Cada upload gasta 1 unidade da cota (limite de 100 por dia).

9. **Descrição** em `CRONICAS SAGRADAS/<pasta do episódio>/descricao_youtube.txt`: a legenda do Instagram, trocando "Siga" por "Inscreva-se".
   **Título**: até 100 caracteres, sem `<` nem `>`. Use o gancho (1ª linha) e encurte se passar.
10. **Duração:** Short é vídeo vertical de **até 3 min**. Acima disso, entra como vídeo normal, na aba "Vídeos". Foi o caso do Ep.02 Pedro, com 3min50,
    e o usuário quis uma **versão curta** só para o YouTube. Para fazer uma:
    - Escolha frases inteiras que não quebrem o arco (digressões, citações secundárias, perguntas repetidas). Mire em ≤ 2min55.
    - Ache o silêncio real de cada ponta com `ffmpeg -ss <s> -t 4 -i voz.mp3 -af silencedetect=noise=-38dB:d=0.12 -f null -`
      e corte no meio dele. O `words.json` erra até ~0,4 s.
    - Crie `timelineShort.ts` com `cuts` em `createEpisodeTimeline`. A voz é emendada sozinha e as palavras de dentro somem.
      Crie também `EpisodeNNShort.tsx`, sem as cenas cortadas e com as transições refeitas nas emendas (máscara pede `exit: "hold"` antes).
      No `Scenes.tsx`, o `useCue` precisa ler a linha do tempo de um contexto (`TimelineCtx`, como no Ep.02), e não do `tl` importado.
      Modelo: `src/ep02/` (composição `Ep02-Pedro-Short`).
    - Revise as emendas com stills e renderize como `cronicas_epNN_<slug>_short.mp4`. Instagram e TikTok continuam com a versão longa.
11. **Agendar no mesmo horário do post do Zernio.** Pegue o horário em `posts_get` (vem em UTC) e converta para São Paulo (UTC−3):
```powershell
python .claude\skills\cronicas\scripts\youtube_upload.py upload entregas\cronicas_epNN_<slug>.mp4 --publish-at AAAA-MM-DDTHH:MM --title '<título>' --description-file "CRONICAS SAGRADAS\<pasta>\descricao_youtube.txt" --tags "catolicos,igreja catolica,biblia,<tema>,fe catolica,cronicas do sagrado"
```
   - No PowerShell, o título vai entre **aspas simples**. Aspas curvas (“ ”) dentro de aspas duplas quebram o comando.
   - O vídeo sobe privado, com `publishAt`, e o YouTube publica sozinho na hora marcada. `--now` publica na hora: só use se o usuário pedir.
   - Sem rótulo de IA: o script manda `containsSyntheticMedia: false`, a mesma decisão tomada para o TikTok.
12. **Conferir:** `youtube_upload.py status <ID>` deve mostrar `private` e o "Publica em" certo. `youtube_upload.py list` mostra os últimos vídeos do canal.
   - **"O login do YouTube venceu":** o app OAuth (projeto `custom-blade-513514-b7`) está em **modo de teste**, e nesse modo o login vence a cada 7 dias.
     Rode `youtube_upload.py auth` em segundo plano. O usuário escolhe a conta akicesagamestuto e clica em Continuar → Selecionar tudo → Continuar.
     Para acabar com isso, publique o app. O Google exige página inicial e política de privacidade no Branding para liberar o botão "Publicar app".

---

## Armadilhas conhecidas

- Python: **não use `python -I`** (esconde as bibliotecas instaladas com `--user`). faster-whisper 1.2.1 + PyAV 19:
  decodifique o áudio com PyAV e passe o array (os scripts já fazem isso).
- ffmpeg/ffprobe não estão no PATH do Bash: `export PATH="$PATH:$(dirname "$(find /c/Users/user/AppData/Local/Microsoft/WinGet -name ffprobe.exe | head -1)")"`.
- `tl.at()` lança erro se a frase não existir — use as palavras exatas da narração (acentos e pontuação são ignorados).
- Mostrar só metade de uma pintura (ex.: painel duplo): `style={{ width: "200%", left: "-100%" }}` + `position` com
  `"100% 20%"` e `origin` `"75% 30%"` (ou `0%`/`25%` para a metade esquerda), senão o zoom puxa o centro errado.
- `WordsAt` reserva espaço para palavras ainda invisíveis: a linha só fica centralizada quando todas aparecem;
  mantenha linhas curtas (tamanho 44–52 para 3 palavras em versaletes).
- Passe `dur` às cenas; não dependa de `useVideoConfig().durationInFrames` dentro de `Sequence`.
- Renders e downloads demorados: sempre em segundo plano.
