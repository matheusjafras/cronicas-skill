"""Crônicas do Sagrado -> YouTube Shorts pela API oficial (YouTube Data API v3), sempre AGENDADO.

Grátis: o upload gasta 1 unidade da cota "Video Uploads" (100 por dia).
As chaves ficam fora do OneDrive e do GitHub, em %USERPROFILE%\\.cronicas-youtube\\
  client_secret.json  (baixado do Google Cloud, cliente "App para computador")
  token.json          (criado pelo comando auth)

  python youtube_upload.py auth
  python youtube_upload.py upload "entregas/EP05 - Confissão/cronicas_ep05_confissao.mp4" --title "..." --description-file legenda.txt --publish-at 2026-11-03T19:30
  (--now no lugar de --publish-at publica na hora; só quando o usuário pedir)
  python youtube_upload.py status VIDEO_ID
  python youtube_upload.py reagendar VIDEO_ID --publish-at 2026-11-03T07:00   (muda o horário de um vídeo já agendado)
  python youtube_upload.py list
  python youtube_upload.py painel   (JSONs do painel em CRONICAS SAGRADAS/painel/)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

sys.stdout.reconfigure(encoding="utf-8")

KEYS = Path.home() / ".cronicas-youtube"
CLIENT_SECRET = KEYS / "client_secret.json"
TOKEN = KEYS / "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    # videos.update (reagendar) não aceita youtube.upload
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
# Opcional, só para o painel (horas assistidas, views de Shorts): sem ela todo o resto funciona.
ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"
# Brasil sem horário de verão desde 2019: São Paulo é sempre UTC-3 (o Windows não traz a base do zoneinfo).
SAO_PAULO = timezone(timedelta(hours=-3))
# O canal era pessoal: o painel só conta o que foi enviado depois do relançamento como Crônicas.
PAINEL_DESDE = "2026-11-01"


def credentials(interactive=False):
    creds = None
    if TOKEN.exists():
        info = json.loads(TOKEN.read_text(encoding="utf-8"))
        granted = set(info.get("scopes", []))
        # login feito antes de uma permissão nova entrar em SCOPES: precisa entrar de novo
        # (o comando auth também refaz o login quando falta a permissão opcional do Analytics)
        if set(SCOPES) <= granted and (ANALYTICS_SCOPE in granted or not interactive):
            creds = Credentials.from_authorized_user_info(info, sorted(granted))
        elif not interactive:
            sys.exit("O login do YouTube precisa ser refeito (permissão nova). Rode: python youtube_upload.py auth")
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            creds = None
            if not interactive:
                sys.exit("O login do YouTube venceu ou foi revogado. Rode: python youtube_upload.py auth")
    if not creds or not creds.valid:
        if not interactive:
            sys.exit("Sem login no YouTube. Rode: python youtube_upload.py auth")
        if not CLIENT_SECRET.exists():
            sys.exit(f"Falta o arquivo {CLIENT_SECRET} (baixe o JSON do cliente OAuth no Google Cloud).")
        # se a pessoa desmarcar a permissão opcional, o login vale assim mesmo
        os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES + [ANALYTICS_SCOPE])
        print("Abrindo o navegador para o login do Google...")
        creds = flow.run_local_server(port=0, prompt="consent")
    KEYS.mkdir(exist_ok=True)
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return creds


def youtube(interactive=False):
    return build("youtube", "v3", credentials=credentials(interactive), cache_discovery=False)


def to_utc(local):
    """'AAAA-MM-DDTHH:MM' no horário de São Paulo -> ISO em UTC para o status.publishAt."""
    when = datetime.fromisoformat(local).replace(tzinfo=SAO_PAULO)
    if when < datetime.now(SAO_PAULO) + timedelta(minutes=15):
        sys.exit(f"Horário {local} já passou ou está perto demais (mínimo 15 min à frente).")
    return when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def abrir_no_chrome(perfil):
    """Faz o login do Google abrir no perfil do Chrome da conta do canal (ex.: 'Profile 10')."""
    chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

    class Chrome(webbrowser.BaseBrowser):
        def open(self, url, new=0, autoraise=True):
            subprocess.Popen([str(chrome), f"--profile-directory={perfil}", url])
            return True

    webbrowser.register("chrome-canal", None, Chrome("chrome-canal"), preferred=True)


def cmd_auth(args):
    if args.chrome_perfil:
        abrir_no_chrome(args.chrome_perfil)
    yt = youtube(interactive=True)
    channels = yt.channels().list(part="snippet", mine=True).execute().get("items", [])
    if not channels:
        sys.exit("Login feito, mas essa conta não tem canal do YouTube.")
    for ch in channels:
        print(f"Conectado ao canal: {ch['snippet']['title']} ({ch['id']})")


def cmd_upload(args):
    video = Path(args.file)
    if not video.exists():
        sys.exit(f"Vídeo não encontrado: {video}")
    description = Path(args.description_file).read_text(encoding="utf-8").strip() if args.description_file else ""
    for name, text, limit in (("título", args.title, 100), ("descrição", description, 5000)):
        if "<" in text or ">" in text:
            sys.exit(f"O YouTube não aceita < ou > no {name}.")
        if len(text.encode("utf-8")) > limit:
            sys.exit(f"O {name} passou de {limit} bytes.")
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    if args.now:
        status = {"privacyStatus": "public"}
    else:
        # fica privado até o publishAt; aí o YouTube torna público sozinho
        status = {"privacyStatus": "private", "publishAt": to_utc(args.publish_at)}

    body = {
        "snippet": {
            "title": args.title,
            "description": description,
            "tags": tags,
            "categoryId": args.category,
            "defaultLanguage": "pt-BR",
            "defaultAudioLanguage": "pt-BR",
        },
        "status": {
            **status,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": False,
        },
    }
    yt = youtube()
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    print(f"Enviando {video.name} ({video.stat().st_size / 1e6:.0f} MB)...")
    response = None
    while response is None:
        progress, response = request.next_chunk(num_retries=5)
        if progress:
            print(f"  {progress.progress() * 100:.0f}%")
    video_id = response["id"]

    if args.thumbnail:
        try:
            yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(args.thumbnail)).execute()
            print("Capa enviada.")
        except HttpError as err:
            print(f"Capa não enviada (o canal precisa estar verificado por telefone): {err.reason}")

    print("Publicado agora." if args.now else f"Agendado: {args.publish_at} (São Paulo)")
    print(f"ID: {video_id}")
    print(f"Link: https://youtube.com/shorts/{video_id}")


def cmd_reagendar(args):
    yt = youtube()
    items = yt.videos().list(part="status", id=args.video_id).execute()["items"]
    if not items:
        sys.exit("Vídeo não encontrado nesse canal.")
    st = items[0]["status"]
    if st["privacyStatus"] != "private" or "publishAt" not in st:
        sys.exit("Esse vídeo não está agendado (já é público ou não tem horário marcado).")
    # atualizar a parte status apaga o que não for enviado: repete os campos graváveis atuais
    keep = ("embeddable", "license", "publicStatsViewable", "selfDeclaredMadeForKids", "containsSyntheticMedia")
    if args.now:
        # tirar o publishAt e tornar público = publica na hora
        status = {**{k: st[k] for k in keep if k in st}, "privacyStatus": "public"}
    else:
        status = {**{k: st[k] for k in keep if k in st}, "privacyStatus": "private", "publishAt": to_utc(args.publish_at)}
    yt.videos().update(part="status", body={"id": args.video_id, "status": status}).execute()
    print("Publicado agora." if args.now else f"Reagendado: {args.publish_at} (São Paulo)")


def cmd_desagendar(args):
    # Para trocar o vídeo de um agendamento: o YouTube não troca o arquivo de um vídeo enviado.
    # Sobe-se o novo e este perde o horário (fica privado). Apagar fica com o usuário, no YouTube Studio.
    yt = youtube()
    items = yt.videos().list(part="status", id=args.video_id).execute()["items"]
    if not items:
        sys.exit("Vídeo não encontrado nesse canal.")
    st = items[0]["status"]
    if st["privacyStatus"] != "private" or "publishAt" not in st:
        sys.exit("Esse vídeo não está agendado (já é público ou não tem horário marcado).")
    keep = ("embeddable", "license", "publicStatsViewable", "selfDeclaredMadeForKids", "containsSyntheticMedia")
    status = {**{k: st[k] for k in keep if k in st}, "privacyStatus": "private"}
    yt.videos().update(part="status", body={"id": args.video_id, "status": status}).execute()
    print("Agendamento cancelado: o vídeo continua privado e não vai ao ar.")


def cmd_status(args):
    items = youtube().videos().list(part="snippet,status,processingDetails", id=args.video_id).execute()["items"]
    if not items:
        sys.exit("Vídeo não encontrado nesse canal.")
    v = items[0]
    st = v["status"]
    print(f"Título: {v['snippet']['title']}")
    print(f"Visibilidade: {st['privacyStatus']}  |  upload: {st['uploadStatus']}")
    if "publishAt" in st:
        local = datetime.fromisoformat(st["publishAt"].replace("Z", "+00:00")).astimezone(SAO_PAULO)
        print(f"Publica em: {local:%d/%m/%Y %H:%M} (São Paulo)")
    for key in ("rejectionReason", "failureReason"):
        if key in st:
            print(f"Problema: {st[key]}")
    if "processingDetails" in v:
        print(f"Processamento: {v['processingDetails'].get('processingStatus')}")


def cmd_list(args):
    yt = youtube()
    channel = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    items = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=args.n).execute()["items"]
    ids = ",".join(i["contentDetails"]["videoId"] for i in items)
    if not ids:
        print("Nenhum vídeo no canal.")
        return
    for v in yt.videos().list(part="snippet,status", id=ids).execute()["items"]:
        st = v["status"]
        when = ""
        if "publishAt" in st:
            local = datetime.fromisoformat(st["publishAt"].replace("Z", "+00:00")).astimezone(SAO_PAULO)
            when = f" -> publica {local:%d/%m %H:%M}"
        print(f"{v['id']}  {st['privacyStatus']:<8}{when}  {v['snippet']['title']}")


def seconds(iso_duration):
    """'PT2M53S' -> 173."""
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration or "")
    if not m:
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + s


def analytics_canal(creds):
    """(horas em vídeos longos nos últimos 365 dias, views de Shorts nos últimos 90 dias) pelo YouTube Analytics.

    (None, None) sem a permissão opcional ou se a API recusar; o painel então mostra só o resto.
    Os números do Analytics chegam com 2 a 3 dias de atraso.
    """
    if ANALYTICS_SCOPE not in (creds.scopes or []):
        print("Horas assistidas: falta a permissão do YouTube Analytics (rode auth de novo).")
        return None, None
    ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    hoje = datetime.now(SAO_PAULO).date()

    def por_tipo(dias, metrica):
        resp = ya.reports().query(ids="channel==MINE", startDate=str(hoje - timedelta(days=dias)), endDate=str(hoje),
                                  metrics=metrica, dimensions="creatorContentType").execute()
        # o tipo vem como VIDEO_ON_DEMAND, SHORTS, LIVE_STREAM...; normaliza para comparar
        return {str(tipo).replace("_", "").lower(): valor for tipo, valor in resp.get("rows", [])}

    try:
        minutos = por_tipo(365, "estimatedMinutesWatched")
        views = por_tipo(90, "views")
    except HttpError as err:
        print(f"Horas assistidas: o YouTube Analytics recusou ({err.status_code}: {err.reason}).")
        return None, None
    print(f"Analytics, minutos por tipo (365 dias): {minutos} | views por tipo (90 dias): {views}")
    horas = sum(v for tipo, v in minutos.items() if tipo in ("videoondemand", "livestream")) / 60
    return round(horas, 1), int(views.get("shorts", 0))


def cmd_painel(args):
    """Exporta os vídeos do canal (só os do Crônicas, enviados desde o relançamento) para o painel."""
    creds = credentials()
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    channel = yt.channels().list(part="contentDetails,statistics", mine=True).execute()["items"][0]
    uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while True:
        page = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
        ids += [i["contentDetails"]["videoId"] for i in page["items"]]
        token = page.get("nextPageToken")
        if not token:
            break
    rows = []
    for start in range(0, len(ids), 50):
        batch = ",".join(ids[start:start + 50])
        for v in yt.videos().list(part="snippet,status,statistics,contentDetails", id=batch).execute()["items"]:
            sn, st, stats = v["snippet"], v["status"], v.get("statistics", {})
            if sn["publishedAt"] < PAINEL_DESDE:
                continue  # vídeos antigos do canal pessoal
            dur = seconds(v["contentDetails"].get("duration"))
            rows.append({
                "video_id": v["id"],
                "titulo": sn["title"],
                "visibilidade": st["privacyStatus"],
                "envio": st.get("uploadStatus"),
                "publica_em": st.get("publishAt"),
                "publicado_em": sn["publishedAt"],
                "duracao_s": dur,
                "views": int(stats.get("viewCount", 0)),
                "curtidas": int(stats.get("likeCount", 0)),
                "comentarios": int(stats.get("commentCount", 0)),
                "link": f"https://youtube.com/{'shorts/' if dur and dur <= 180 else 'watch?v='}{v['id']}",
            })
    rows.sort(key=lambda r: r["publica_em"] or r["publicado_em"])
    cs = channel["statistics"]
    # Metas do Programa de Parcerias. O Analytics chega com 2-3 dias de atraso; a contagem direta (views dos Shorts
    # públicos postados em 90 dias) está em dia mas não vê Shorts mais antigos. Vale a maior das duas.
    horas, shorts_analytics = analytics_canal(creds)
    noventa = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
    shorts_90d = max(shorts_analytics or 0, sum(r["views"] for r in rows if r["visibilidade"] == "public"
                                                and (r["duracao_s"] or 0) <= 180 and r["publicado_em"] >= noventa))
    canal = [{
        "inscritos": int(cs.get("subscriberCount", 0)),
        "views_canal": int(cs.get("viewCount", 0)),
        "videos_cronicas": len(rows),
        "shorts_views_90d": shorts_90d,
        "horas_longos_365d": horas,
    }]
    out = Path(args.saida)
    out.mkdir(parents=True, exist_ok=True)
    (out / "youtube_videos.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "youtube_canal.json").write_text(json.dumps(canal, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rows)} vídeos e o resumo do canal salvos em {out}")


def main():
    parser = argparse.ArgumentParser(description="Crônicas do Sagrado -> YouTube Shorts (agendado)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    au = sub.add_parser("auth", help="login no Google (uma vez)")
    au.add_argument("--chrome-perfil", help='pasta do perfil do Chrome da conta do canal, ex.: "Profile 10"')
    au.set_defaults(func=cmd_auth)
    up = sub.add_parser("upload", help="envia e agenda um Short")
    up.add_argument("file")
    up.add_argument("--title", required=True)
    up.add_argument("--description-file")
    when = up.add_mutually_exclusive_group(required=True)
    when.add_argument("--publish-at", help="AAAA-MM-DDTHH:MM, horário de São Paulo")
    when.add_argument("--now", action="store_true", help="publica na hora (só se o usuário pedir)")
    up.add_argument("--tags", help="separadas por vírgula")
    up.add_argument("--thumbnail")
    up.add_argument("--category", default="27", help="27 = Educação")
    up.set_defaults(func=cmd_upload)
    stat = sub.add_parser("status", help="situação de um vídeo")
    stat.add_argument("video_id")
    stat.set_defaults(func=cmd_status)
    re_ = sub.add_parser("reagendar", help="muda o horário de um vídeo já agendado")
    re_.add_argument("video_id")
    quando = re_.add_mutually_exclusive_group(required=True)
    quando.add_argument("--publish-at", help="AAAA-MM-DDTHH:MM, horário de São Paulo")
    quando.add_argument("--now", action="store_true", help="publica na hora um vídeo agendado (só se o usuário pedir)")
    re_.set_defaults(func=cmd_reagendar)
    de = sub.add_parser("desagendar", help="tira o horário de um vídeo agendado (fica privado, não apaga)")
    de.add_argument("video_id")
    de.set_defaults(func=cmd_desagendar)
    ls = sub.add_parser("list", help="últimos vídeos do canal e agendamentos")
    ls.add_argument("-n", type=int, default=10)
    ls.set_defaults(func=cmd_list)
    pn = sub.add_parser("painel", help="exporta vídeos e números do canal para o painel")
    pn.add_argument("--saida", default="CRONICAS SAGRADAS/painel")
    pn.set_defaults(func=cmd_painel)
    args = parser.parse_args()
    try:
        args.func(args)
    except HttpError as err:
        sys.exit(f"Erro do YouTube ({err.status_code}): {err.reason}")


if __name__ == "__main__":
    main()
