"""Crônicas do Sagrado -> Página do Facebook pela Graph API oficial, sempre AGENDADO.

Grátis. As chaves ficam fora do OneDrive e do GitHub, em %USERPROFILE%\\.cronicas-facebook\\
  page_token.json  (criado pelo comando auth; o token da Página não vence)

  python facebook_upload.py auth
  python facebook_upload.py upload entregas/cronicas_ep05_x.mp4 --title "..." --description-file legenda.txt --publish-at 2026-11-05T07:00
  (--now no lugar de --publish-at publica na hora; só quando o usuário pedir)
  python facebook_upload.py status VIDEO_ID
  python facebook_upload.py list
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

KEYS = Path.home() / ".cronicas-facebook"
PAGE_TOKEN = KEYS / "page_token.json"
PAGE_ID = "1521846121001422"  # Página Crônicas do Sagrado (na API; o link profile.php usa 61596302966647)
APP_ID = "1162878049422733"  # app "Cronicas Publicador" (Meta for Developers, modo de desenvolvimento)
GRAPH = "https://graph.facebook.com/v26.0"
GRAPH_VIDEO = "https://graph-video.facebook.com/v26.0"
SAO_PAULO = timezone(timedelta(hours=-3))


def api(method, url, **kwargs):
    resp = requests.request(method, url, timeout=600, **kwargs)
    data = resp.json() if resp.content else {}
    if resp.status_code >= 400 or "error" in data:
        err = data.get("error", {})
        sys.exit(f"Erro do Facebook ({resp.status_code}): {err.get('message', resp.text[:300])}")
    return data


def quando_fb(valor):
    """scheduled_publish_time vem como número (epoch) ou como texto ISO, conforme o campo."""
    if valor is None:
        return None
    if str(valor).isdigit():
        return datetime.fromtimestamp(int(valor), timezone.utc)
    return datetime.strptime(str(valor), "%Y-%m-%dT%H:%M:%S%z")


ENVIADOS = Path(__file__).resolve().parents[4] / "CRONICAS SAGRADAS" / "painel" / "facebook_ids.json"


def guardar_id(video_id):
    """A lista de vídeos da Página não traz agendados nem os que estão processando: o painel lê por id."""
    ids = json.loads(ENVIADOS.read_text(encoding="utf-8")) if ENVIADOS.exists() else []
    if video_id not in ids:
        ids.append(video_id)
        ENVIADOS.write_text(json.dumps(ids, indent=1), encoding="utf-8")


def page():
    if not PAGE_TOKEN.exists():
        sys.exit("Sem login na Página. Rode: python facebook_upload.py auth")
    return json.loads(PAGE_TOKEN.read_text(encoding="utf-8"))


PAGINA_LOGIN = """<!doctype html><meta charset="utf-8"><title>Crônicas: login do Facebook</title>
<p id="m">Conectando a Página...</p>
<script>
fetch('/token', {method: 'POST', body: location.hash.slice(1)})
  .then(r => r.text()).then(t => { document.getElementById('m').textContent = t; history.replaceState(null, '', '/'); });
</script>"""


def pagina_com_token(longo):
    """Acha a Página do canal e o token dela: pelas Páginas da pessoa ou pelos portfólios empresariais."""
    contas = api("GET", f"{GRAPH}/me/accounts", params={"access_token": longo, "fields": "id,name,access_token", "limit": 100})["data"]
    print("Páginas da pessoa:", ", ".join(f"{p['name']} ({p['id']})" for p in contas), flush=True)
    # a Página nova pode ter, na API, um id diferente do que aparece no link profile.php
    achada = next((p for p in contas if p["id"] == PAGE_ID or "sagrado" in p["name"].lower()), None)
    if achada:
        return achada
    # Páginas novas, ligadas a um portfólio, às vezes só aparecem pelo portfólio
    negocios = api("GET", f"{GRAPH}/me/businesses", params={"access_token": longo, "fields": "id"}).get("data", [])
    for neg in negocios:
        for aresta in ("owned_pages", "client_pages"):
            resp = requests.get(f"{GRAPH}/{neg['id']}/{aresta}", timeout=60,
                                params={"access_token": longo, "fields": "id,name,access_token"}).json()
            print(f"Portfólio {neg['id']} ({aresta}):", ", ".join(f"{p['name']} ({p['id']})" for p in resp.get("data", [])) or resp.get("error", {}).get("message", "nenhuma"), flush=True)
            achada = next((p for p in resp.get("data", []) if p["id"] == PAGE_ID or "sagrado" in p["name"].lower()), None)
            if achada and achada.get("access_token"):
                return achada
    return None


def cmd_auth(args):
    """Login do Facebook: o token chega direto neste script (servidor local), nunca passa pela conversa."""
    import http.server
    import urllib.parse
    import webbrowser

    resultado = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def responder(self, texto, tipo="text/plain"):
            corpo = texto.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", f"{tipo}; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_GET(self):
            self.responder(PAGINA_LOGIN, "text/html")

        def do_POST(self):
            dados = urllib.parse.parse_qs(self.rfile.read(int(self.headers["Content-Length"] or 0)).decode())
            longo = (dados.get("long_lived_token") or dados.get("access_token") or [""])[0]
            if not longo:
                resultado["erro"] = dados.get("error_description", ["login cancelado"])[0]
                self.responder(f"Não deu certo: {resultado['erro']}")
                return
            try:
                pagina = pagina_com_token(longo)
            except (SystemExit, Exception) as err:  # api() sai com sys.exit; numa thread isso sumiria calado
                resultado["erro"] = str(err)
                self.responder(f"Não deu certo: {err}")
                return
            if not pagina:
                resultado["erro"] = "o login não dá acesso à Página Crônicas do Sagrado"
                self.responder("O login funcionou, mas não dá acesso à Página Crônicas do Sagrado.")
                return
            KEYS.mkdir(exist_ok=True)
            PAGE_TOKEN.write_text(json.dumps({"page_id": pagina["id"], "page_name": pagina["name"],
                                              "access_token": pagina["access_token"]}, ensure_ascii=False), encoding="utf-8")
            resultado["pagina"] = pagina["name"]
            self.responder(f"Pronto! Página conectada: {pagina['name']}. Pode fechar esta aba.")

    # várias conexões ao mesmo tempo: o Chrome abre conexões ociosas que travariam um servidor simples
    servidor = http.server.ThreadingHTTPServer(("localhost", args.porta), Handler)
    servidor.daemon_threads = True
    url = "https://www.facebook.com/v26.0/dialog/oauth?" + urllib.parse.urlencode({
        "client_id": APP_ID, "redirect_uri": f"http://localhost:{args.porta}/", "response_type": "token",
        "scope": "pages_show_list,pages_manage_posts,pages_read_engagement,read_insights,business_management",
    })
    print(f"Abra para fazer o login: {url}", flush=True)
    if not args.sem_navegador:
        webbrowser.open(url)
    import threading
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    while not resultado:
        threading.Event().wait(0.5)
    servidor.shutdown()
    servidor.server_close()
    if "erro" in resultado:
        sys.exit(f"Login do Facebook: {resultado['erro']}")
    print(f"Conectado à Página: {resultado['pagina']}")


def cmd_upload(args):
    video = Path(args.file)
    if not video.exists():
        sys.exit(f"Vídeo não encontrado: {video}")
    pg = page()
    description = Path(args.description_file).read_text(encoding="utf-8").strip() if args.description_file else ""
    data = {"access_token": pg["access_token"], "title": args.title, "description": description}
    if args.now:
        data["published"] = "true"
    else:
        when = datetime.fromisoformat(args.publish_at).replace(tzinfo=SAO_PAULO)
        if when < datetime.now(SAO_PAULO) + timedelta(minutes=15):
            sys.exit(f"Horário {args.publish_at} já passou ou está perto demais (mínimo 15 min à frente).")
        # o Facebook guarda privado e publica sozinho na hora marcada
        data["published"] = "false"
        data["scheduled_publish_time"] = str(int(when.timestamp()))
    tamanho = video.stat().st_size
    print(f"Enviando {video.name} ({tamanho / 1e6:.0f} MB)...")
    # envio em partes: o envio direto recusa arquivos grandes (413)
    url = f"{GRAPH_VIDEO}/{pg['page_id']}/videos"
    token = pg["access_token"]
    inicio = api("POST", url, data={"access_token": token, "upload_phase": "start", "file_size": str(tamanho)})
    sessao, video_id = inicio["upload_session_id"], inicio["video_id"]
    de, ate = int(inicio["start_offset"]), int(inicio["end_offset"])
    with video.open("rb") as f:
        while de < ate:
            f.seek(de)
            parte = api("POST", url, data={"access_token": token, "upload_phase": "transfer",
                                          "upload_session_id": sessao, "start_offset": str(de)},
                        files={"video_file_chunk": ("parte", f.read(ate - de), "application/octet-stream")})
            de, ate = int(parte["start_offset"]), int(parte["end_offset"])
            print(f"  {de * 100 // tamanho}%", flush=True)
    api("POST", url, data={**data, "upload_phase": "finish", "upload_session_id": sessao})
    guardar_id(video_id)
    print("Publicado agora." if args.now else f"Agendado: {args.publish_at} (São Paulo)")
    print(f"ID: {video_id}")
    print(f"Link: https://www.facebook.com/{pg['page_id']}/videos/{video_id}")


def cmd_status(args):
    pg = page()
    v = api("GET", f"{GRAPH}/{args.video_id}", params={
        "access_token": pg["access_token"],
        "fields": "title,published,scheduled_publish_time,status,permalink_url,created_time"})
    print(f"Título: {v.get('title', '')}")
    print(f"Publicado: {'sim' if v.get('published') else 'não'}  |  status: {v.get('status', {}).get('video_status')}")
    if v.get("scheduled_publish_time"):
        print(f"Publica em: {quando_fb(v['scheduled_publish_time']).astimezone(SAO_PAULO):%d/%m/%Y %H:%M} (São Paulo)")
    if v.get("permalink_url"):
        print(f"Link: https://www.facebook.com{v['permalink_url']}")


def cmd_list(args):
    pg = page()
    vids = api("GET", f"{GRAPH}/{pg['page_id']}/videos", params={
        "access_token": pg["access_token"], "type": "uploaded", "limit": args.n,
        "fields": "id,title,published,scheduled_publish_time,created_time"})["data"]
    if not vids:
        print("Nenhum vídeo na Página.")
    for v in vids:
        when = ""
        if v.get("scheduled_publish_time"):
            when = f" -> publica {quando_fb(v['scheduled_publish_time']).astimezone(SAO_PAULO):%d/%m %H:%M}"
        print(f"{v['id']}  {'público ' if v.get('published') else 'agendado'}{when}  {v.get('title', '')}")


def cmd_painel(args):
    """Exporta os vídeos e os seguidores da Página para o painel (mesmo formato do YouTube)."""
    pg = page()
    token = pg["access_token"]
    campos = "id,title,description,published,scheduled_publish_time,created_time,updated_time,permalink_url,likes.summary(true).limit(0),comments.summary(true).limit(0)"
    vids = api("GET", f"{GRAPH}/{pg['page_id']}/videos", params={
        "access_token": token, "type": "uploaded", "limit": 100, "fields": campos})["data"]
    vistos = {v["id"] for v in vids}
    for vid in (json.loads(ENVIADOS.read_text(encoding="utf-8")) if ENVIADOS.exists() else []):
        if vid not in vistos:
            extra = requests.get(f"{GRAPH}/{vid}", timeout=60, params={"access_token": token, "fields": campos}).json()
            if "id" in extra:
                vids.append(extra)
    linhas = []
    for v in vids:
        # views: o campo antigo nem sempre vem; as métricas de vídeo da Página são a fonte certa
        # vídeos verticais viram Reels: a métrica deles é blue_reels_play_count; vídeo comum usa total_video_views
        valores = []
        for metrica in ("blue_reels_play_count", "total_video_views"):
            resp = requests.get(f"{GRAPH}/{v['id']}/video_insights", timeout=60,
                                params={"access_token": token, "metric": metrica}).json()
            valores = [x["values"][0]["value"] for x in resp.get("data", []) if x.get("values")]
            if valores:
                break
        agendado = not v.get("published") and v.get("scheduled_publish_time")
        linhas.append({
            "video_id": v["id"],
            "titulo": v.get("title") or (v.get("description") or "").split("\n")[0][:100],
            "visibilidade": "public" if v.get("published") else ("scheduled" if agendado else "private"),
            "publica_em": quando_fb(v["scheduled_publish_time"]).strftime("%Y-%m-%dT%H:%M:%SZ") if agendado else None,
            "publicado_em": v.get("created_time"),
            "views": int(valores[0]) if valores else None,
            "curtidas": v.get("likes", {}).get("summary", {}).get("total_count"),
            "comentarios": v.get("comments", {}).get("summary", {}).get("total_count"),
            "link": f"https://www.facebook.com{v['permalink_url']}" if v.get("permalink_url") else f"https://www.facebook.com/{pg['page_id']}/videos/{v['id']}",
        })
    linhas.sort(key=lambda r: r["publica_em"] or r["publicado_em"] or "")
    info = api("GET", f"{GRAPH}/{pg['page_id']}", params={"access_token": token, "fields": "followers_count,fan_count"})
    pagina = [{"seguidores": info.get("followers_count", info.get("fan_count", 0)), "videos": len(linhas)}]
    out = Path(args.saida)
    out.mkdir(parents=True, exist_ok=True)
    (out / "facebook_videos.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "facebook_pagina.json").write_text(json.dumps(pagina, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(linhas)} vídeos e os seguidores da Página salvos em {out}")


def main():
    parser = argparse.ArgumentParser(description="Crônicas do Sagrado -> Página do Facebook (agendado)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    au = sub.add_parser("auth", help="login do Facebook e token da Página (uma vez)")
    au.add_argument("--porta", type=int, default=8765)
    au.add_argument("--sem-navegador", action="store_true", help="só mostra o link, não abre o navegador")
    au.set_defaults(func=cmd_auth)
    up = sub.add_parser("upload", help="envia e agenda um vídeo na Página")
    up.add_argument("file")
    up.add_argument("--title", required=True)
    up.add_argument("--description-file")
    when = up.add_mutually_exclusive_group(required=True)
    when.add_argument("--publish-at", help="AAAA-MM-DDTHH:MM, horário de São Paulo")
    when.add_argument("--now", action="store_true", help="publica na hora (só se o usuário pedir)")
    up.set_defaults(func=cmd_upload)
    st = sub.add_parser("status", help="situação de um vídeo")
    st.add_argument("video_id")
    st.set_defaults(func=cmd_status)
    ls = sub.add_parser("list", help="vídeos da Página e agendamentos")
    ls.add_argument("-n", type=int, default=10)
    ls.set_defaults(func=cmd_list)
    pn = sub.add_parser("painel", help="exporta vídeos e seguidores da Página para o painel")
    pn.add_argument("--saida", default="CRONICAS SAGRADAS/painel")
    pn.set_defaults(func=cmd_painel)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
