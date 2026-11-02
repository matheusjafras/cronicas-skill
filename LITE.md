# /cronicas lite — episódios leves, em lote

Formato para **volume**: vários episódios de uma vez, sem código por cena. Cada episódio é um arquivo de dados
(`projeto/src/lite/epNN_<slug>/episode.json`) e o template `projeto/src/lite/` monta tudo sozinho: molduras, câmera
sobre a obra, títulos por máscara, destaques no tempo da fala, citação em pergaminho, lista com ícones, fecho com a
assinatura, transições, efeitos sonoros e trilha. O ganho é na **produção** (nenhum código por cena, revisão curta, tudo
em lote). O **render custa o mesmo** que o completo em modo `fast` (mesmo custo por quadro em trechos medidos lado a
lado em 01/11/2026). Render inteiro pela fila: **13,2 min para 2min51** → ~9 min por vídeo de 1min50. Desligar grão,
legenda ou partículas não mudou nada: o custo é o piso da máquina para desenhar e codificar 1080×1920. Só a resolução
muda isso (escala 0,75 = 810×1440: −25%, imagem menos nítida; só com o ok do usuário).
Não anime o fundo de tela cheia (zoom no fundo desfocado): o MP4 triplicou de tamanho (18 Mbps, 378 MB para 2min51).
O `/cronicas` completo continua para episódios especiais, com motion feito à mão.

Valem todas as regras do canal da SKILL.md: fidelidade teológica (etapa 3), obras históricas reais com crédito (etapa 2),
voz Johnes Bittar e preço antes de gerar (etapa 4), legenda `plain`, nada de número de episódio na tela, publicação
sempre **agendada** (etapa 8).

## Como chamar

| Comando | O que faz |
|---|---|
| `/cronicas lite` | lote de **3** episódios do zero: temas → roteiros → obras → narração → blocos → revisão → fila de render → agendamento |
| `/cronicas lite <N>` ou `/cronicas lite <tema>; <tema>; …` | lote com N episódios, ou com os temas dados |
| `/cronicas lite ajustar <epNN> <pedido>` | muda o `episode.json` daquele episódio, confere e renderiza só ele |

Mostre o progresso do lote no task list (uma linha por etapa, não por episódio). Faça as etapas de **todos** os episódios
juntas (todos os roteiros, depois todas as obras, depois todas as narrações), assim o usuário aprova uma vez só por etapa.

---

## 1. Temas e numeração

- Use os temas que o usuário der. Sem temas, proponha N em uma linha cada (personagem/pergunta + gancho), sem repetir
  episódios que já existem (`CRONICAS SAGRADAS/` e `projeto/src/ep*`, `projeto/src/lite/ep*`).
- Numeração interna: continue do maior `epNN` existente. Slug sem acentos (`sao_jose`, `as_bodas_de_cana`).

## 2. Roteiros (Claude escreve)

- **210–250 palavras** (≈ 1min30–1min50 na voz do Johnes, ~2,3 palavras/s). Nunca acelere a voz para caber.
- Estrutura: a que o usuário mandar; sem estrutura, as 7 batidas do guia de estilo
  (doc https://claude.ai/artifact/Dm1bsJ4gUpWErqHTwWxYpq): gancho em pergunta → contexto bíblico (com referência) →
  o detalhe que muda tudo → o que a Igreja ensina (Catecismo, Padres, papas) → virada → aplicação na vida → pergunta final.
- Frases curtas, uma ideia por frase (cada frase vira um bloco de 4–9 s). Fidelidade teológica: confira cada afirmação,
  cite referências no formato brasileiro (Lc 16,19-31; Catecismo § 633); hipótese não vira fato.
- Mostre os N roteiros juntos (um bloco de código cada, com a contagem de palavras) e **espere o ok** antes da narração.
  Aprovados, salve cada um em `CRONICAS SAGRADAS/epNN_<slug>/narracao_oficial.txt` (passo 3 cria a pasta).

## 3. Criar os episódios

```bash
cd "RAIZ" && python .claude/skills/cronicas/scripts/new_lite.py . <nº> <slug>
```
Cria `CRONICAS SAGRADAS/epNN_<slug>/` (`narracao_oficial.txt`, `obras_originais/`, `creditos_e_fontes.md`),
`projeto/public/lite/epNN_<slug>/` e `projeto/src/lite/epNN_<slug>/episode.json` (id da composição `EpNN-Slug`).

## 4. Obras (Claude procura)

- **Só obras históricas reais em domínio público** (nada de IA): Wikimedia Commons, The Met Open Access, Art Institute of
  Chicago, Cleveland Museum of Art Open Access, National Gallery of Art. Fotos de papas e santos recentes: só CC BY/CC BY-SA,
  com autor e licença na tela.
- 5–8 obras por episódio (a mesma obra pode voltar com outro enquadramento). Prefira ≥ 1500 px no lado maior.
- Baixe os originais para `CRONICAS SAGRADAS/epNN_<slug>/obras_originais/` com nome curto, que vira a chave (`bassano_rico_lazaro.jpg`).
  Wikimedia com HTTP 429: use o endereço direto `upload.wikimedia.org/wikipedia/commons/<md5[0]>/<md5[:2]>/<arquivo>`.
- Anote cada obra em `creditos_e_fontes.md` (obra, autoria, data, acervo, licença, URL, blocos).
- Prepare (reduz para ≤ 1800 px, gera o fundo desfocado e preenche `arts` no JSON):
```bash
python .claude/skills/cronicas/scripts/prep_art.py "CRONICAS SAGRADAS/epNN_<slug>/obras_originais" projeto/public/lite/epNN_<slug> projeto/src/lite/epNN_<slug>/episode.json
```
- Preencha `title` (nome da obra em português) e `meta` (`Artista · data · acervo`; CC BY: `foto: Autor · CC BY 2.0`) de cada obra.
- Olhe as obras (Read) antes de escrever os blocos: o que tem em cada uma, onde estão rostos e detalhes (para `focus`).

## 5. Narração (gasta créditos)

1. `creative_generate_speech` com `estimate_only: true` para cada roteiro → diga o total do lote numa linha
   (≈ 1 crédito por caractere; um roteiro de 250 palavras ≈ 1.700 créditos).
2. Gere as N narrações (podem ir em paralelo) como na etapa 4 da SKILL.md (voz `sJfod1k0iiI5CA9IP0R2`, `eleven_v4`, 1 take,
   tags em inglês). Baixe para `projeto/public/voiceover/epNN_<slug>.mp3`.
3. Tempo das palavras de todos, **em sequência, num só comando em segundo plano** (a CPU é fraca):
```bash
python .claude/skills/cronicas/scripts/align_words.py projeto/public/voiceover/epNN_<slug>.mp3 "CRONICAS SAGRADAS/epNN_<slug>/narracao_oficial.txt" projeto/src/lite/epNN_<slug>/words.json
```

## 6. Blocos (`episode.json`)

Um bloco por frase (4–9 s de fala). `anchor` = primeiras palavras exatas da frase que abre o bloco; `at` = palavra ou
trecho falado **dentro** do bloco, no momento em que o texto aparece. Acentos e pontuação são ignorados; as frases são
procuradas em sequência, então repetições não se confundem.

| `type` | Para quê | Campos |
|---|---|---|
| `art` | a maior parte (~60%): obra na moldura com câmera lenta | `art`, `highlights` [{`text`,`at`}], `kicker`, `title`, `ref`, `focus` [x,y], `frame`, `camera`, `tone` |
| `title` | gancho, perguntas, viradas | `lines` [{`text`,`at`}] (até 3), `kicker`, `sub`, `art` (fundo), `tone` |
| `quote` | Bíblia, Catecismo, Padres, papas | `text` (idêntico à narração → palavra a palavra no tempo da fala), `ref`, `kicker`, `art`, `tone` |
| `list` | 2–4 itens, comparações, passos | `items` [{`text`,`at`,`icon`}], `title`, `art`, `tone` |
| `end` | sempre o último bloco: frases finais + assinatura | `lines` [{`text`,`at`}], `art` (medalhão) |

Regras de texto: destaques e linhas de `title` em CAIXA ALTA, até 3 palavras (≤ 24 caracteres); `title` de obra ≤ 22
caracteres; `kicker` curto (fonte, livro, tema). A 1ª linha de um `title` deve ser falada até ~1,5 s depois da âncora;
se não for, ponha um `kicker`. `list` sem `title` começa com a tela vazia até o 1º item: dê sempre um `title`. Nunca número de episódio na tela.

Tons (`tone`) seguem o arco: `night`/`sepia` (drama, gancho) → `wine` (pecado, juízo) → `blue`/`green` (doutrina, graça)
→ fecho claro (automático no `end`). `parchment`/`light` só em `title` de virada.

Automático (só sobrescreva se precisar): moldura (`gold`, `arch`, `wood`, `medallion`, `darkArch`, `torn`; `gothic` só
à mão — o mainel cruza a obra), câmera (`pan` em obras deitadas; `in`/`out` nas em pé; `in` quando há `focus`),
transições sem repetir, sopro nas transições, papel nas citações, pena nos destaques e itens, sino no fim.
Ícones de `list`: os nomes de `ICONS` na SKILL.md (`check`, `xis`, `olho`, `cruz`, `biblia`, `livro`, `pergaminho`, `coracao`…).
Pausas antes de revelações: `pauses` [{`afterMs`, `ms`}] (ms do áudio original). Trilha: `music` (padrão
`audio/trilha_medieval.wav`, em loop).

Modelo completo: `projeto/src/lite/teste_ep04/episode.json` (o Ep. 04 refeito no lite).

Depois de escrever os blocos:
```bash
python .claude/skills/cronicas/scripts/new_lite.py . --registry
python .claude/skills/cronicas/scripts/check_lite.py projeto/src/lite/epNN_<slug>
```
Corrija até "ok". Blocos `longo` (> 12 s): divida. `curto` (< 2,5 s): junte ao vizinho.

## 7. Revisão rápida (obrigatória)

```bash
cd projeto && npx tsc --noEmit
node scripts/stills.mjs EpNN-<Slug> out/stills_epNN <quadros para revisão do check_lite>
python ../.claude/skills/cronicas/scripts/review_sheet.py out/stills_epNN
```
Abra as folhas com Read. Procure: tela vazia, rosto cortado (ajuste `focus`), texto longo demais, obra repetida em
blocos seguidos, legenda ilegível. Corrija só no JSON.

## 8. Render em fila

```bash
cd projeto && node scripts/render_queue.mjs EpNN-A EpNN-B EpNN-C
```
Sempre em segundo plano. Um bundle só, um episódio depois do outro (o notebook é um i3 de 2 núcleos: render em paralelo
não ganha tempo e pode travar por memória). Conte ~9 min por episódio de 1min50 (um lote de 3 ≈ 30 min). A fila põe um
teto de 8 Mbps (um vídeo de 1min50 fica perto de 110 MB; o Instagram aceita até 300 MB). Cada MP4 vai para `entregas/EPNN - <Nome>/cronicas_epNN_<slug>.mp4`
(crie antes a pasta com o nome acentuado; sem ela, a fila cria uma a partir do id, sem acentos) e entra no `entregas/LEIA-ME.txt`; o tempo de cada um
fica em `projeto/out/fila_render.log`. Nunca pare a fila no meio de um render. Lotes grandes: sugira deixar à noite.
Depois: ffprobe (1080×1920, 30 fps, h264 + aac), 3 quadros de cada MP4 para conferir, `SendUserFile` com os vídeos.

## 9. Publicação

Etapa 8 da SKILL.md para cada episódio, em ordem: a fila do Zernio pega os próximos horários livres (1 por dia, 7h).
Mostre as N legendas + os horários juntos e peça **um** "sim" para o lote (o TikTok exige esse sim antes de
`contentPreviewConfirmed`/`expressConsentGiven`).
