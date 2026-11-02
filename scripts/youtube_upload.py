"""Crônicas do Sagrado -> YouTube Shorts pela API oficial (YouTube Data API v3), sempre AGENDADO.

Grátis: o upload gasta 1 unidade da cota "Video Uploads" (100 por dia).
As chaves ficam fora do OneDrive e do GitHub, em %USERPROFILE%\\.cronicas-youtube\\
  client_secret.json  (baixado do Google Cloud, cliente "App para computador")
  token.json          (criado pelo comando auth)

  python youtube_upload.py auth
  python youtube_upload.py upload entregas/cronicas_ep05_x.mp4 --title "..." --description-file legenda.txt --publish-at 2026-11-03T19:30
  (--now no lugar de --publish-at publica na hora; só quando o usuário pedir)
  python youtube_upload.py status VIDEO_ID
  python youtube_upload.py list
"""
import argparse
import sys
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
]
# Brasil sem horário de verão desde 2019: São Paulo é sempre UTC-3 (o Windows não traz a base do zoneinfo).
SAO_PAULO = timezone(timedelta(hours=-3))


def credentials(interactive=False):
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES) if TOKEN.exists() else None
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
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
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


def cmd_auth(args):
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


def main():
    parser = argparse.ArgumentParser(description="Crônicas do Sagrado -> YouTube Shorts (agendado)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth", help="login no Google (uma vez)").set_defaults(func=cmd_auth)
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
    ls = sub.add_parser("list", help="últimos vídeos do canal e agendamentos")
    ls.add_argument("-n", type=int, default=10)
    ls.set_defaults(func=cmd_list)
    args = parser.parse_args()
    try:
        args.func(args)
    except HttpError as err:
        sys.exit(f"Erro do YouTube ({err.status_code}): {err.reason}")


if __name__ == "__main__":
    main()
