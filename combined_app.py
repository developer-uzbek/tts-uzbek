"""Uzbekcha TTS — Main application: website + API + Telegram bot in a single process."""
import io
import hmac
import os
import re
import time
import json
import threading
from collections import deque
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory, make_response, Response
from flask_cors import CORS

import core
from config import (
    PROJECT_NAME, PROJECT_VERSION, PROJECT_DESCRIPTION,
    PUBLIC_BASE_URL, GITHUB_URL, BOT_USERNAME, BOT_URL,
    PORT, RATE_PER_MIN, DEFAULT_AUDIO_FILENAME, MAX_CHARS,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
START = time.time()

app = Flask(__name__, static_folder=None)
CORS(app, expose_headers=["Content-Disposition"])

_hits = {}


def check_rate(ip):
    if not RATE_PER_MIN:
        return
    now = time.time()
    q = _hits.setdefault(ip, deque())
    while q and q[0] < now - 60:
        q.popleft()
    if len(q) >= RATE_PER_MIN:
        raise core.Busy(f"Too many requests! Maximum {RATE_PER_MIN} new texts per minute per IP. Please wait.")
    q.append(now)
    if len(_hits) > 5000:
        for k in [k for k, v in _hits.items() if not v or v[-1] < now - 60]:
            _hits.pop(k, None)


def client_ip():
    return (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
    )


def payload():
    d = request.args.to_dict()
    d.update(request.form.to_dict())
    j = request.get_json(silent=True)
    if isinstance(j, dict):
        d.update(j)
    return d


def fail(msg, code):
    return jsonify({"status": "error", "message": msg}), code


def tts_response(d):
    text = str(d.get("text") or d.get("q") or d.get("r") or "").strip()
    if not text:
        return fail("Text is required. Example: /?q=Salom", 400)
    if len(text) > MAX_CHARS:
        return fail(
            f"Text too long: {len(text)} chars (max {MAX_CHARS} per request). Split into smaller parts.",
            413,
        )
    try:
        o = core.opts(d)
        sig = str(d.get("sig") or "")
        trusted = bool(sig) and hmac.compare_digest(sig, core.sign(text, o["voice"]))
        data = core.synth(text, o, on_miss=None if trusted else (lambda: check_rate(client_ip())))
    except core.Busy as exc:
        r = jsonify({"status": "error", "message": str(exc)})
        r.status_code, r.headers["Retry-After"] = 429, "10"
        return r
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        print(f"❌ TTS error: {exc}", flush=True)
        return fail(str(exc), 502)
    name = (
        re.sub(r"[^A-Za-z0-9_\- ]+", "", str(d.get("filename") or d.get("name") or ""))
        .strip()
        .replace(" ", "_")
        or DEFAULT_AUDIO_FILENAME
    )
    dl = str(d.get("dl", "")).lower() in {"1", "true", "yes"}
    return send_file(
        io.BytesIO(data),
        mimetype="audio/mpeg",
        as_attachment=dl,
        download_name=f"{name}.mp3",
        conditional=True,
        max_age=86400,
    )


# ─── Page routes ───

@app.route("/")
def index():
    if "q" in request.args or "r" in request.args:
        return tts_response(request.args.to_dict())
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/tts.mp3")
def mp3():
    """Direct MP3 endpoint: /tts.mp3?q=Salom — convenient for <audio> tags and Telegram inline."""
    return tts_response(request.args.to_dict())


@app.route("/guide")
def guide():
    return send_from_directory(BASE_DIR, "guide.html")


@app.route("/theme.css")
def theme_css():
    return send_from_directory(BASE_DIR, "theme.css", mimetype="text/css")


@app.route("/tts.py")
def cli_script():
    return send_from_directory(BASE_DIR, "tts.py", mimetype="text/plain; charset=utf-8")


# ─── API routes ───

@app.route("/api/tts", methods=["GET", "POST"])
@app.route("/api/tts/quick", methods=["GET", "POST"])
def api_tts():
    """Generate TTS audio. Accepts JSON body or query parameters."""
    return tts_response(payload())


@app.route("/api/voices")
def api_voices():
    """Return available voices, styles, and service metadata."""
    return jsonify({
        "status": "success",
        "service": PROJECT_NAME,
        "version": PROJECT_VERSION,
        "app_url": PUBLIC_BASE_URL,
        "bot_url": BOT_URL,
        "github_url": GITHUB_URL,
        "max_chars": MAX_CHARS,
        "voices": core.voices(),
        "styles": [{"id": k, "name": v[0]} for k, v in core.STYLES.items()],
    })


@app.route("/api/info")
def api_info():
    """Return service metadata for AI agents and integrations."""
    return jsonify({
        "service": PROJECT_NAME,
        "description": PROJECT_DESCRIPTION,
        "version": PROJECT_VERSION,
        "website": PUBLIC_BASE_URL,
        "github": GITHUB_URL,
        "telegram_bot": BOT_URL,
        "max_chars_per_request": MAX_CHARS,
        "supported_languages": ["uz", "ru", "en", "tr", "kk"],
        "primary_language": "uz",
        "output_format": "audio/mpeg (MP3)",
        "endpoints": {
            "tts": f"{PUBLIC_BASE_URL}/api/tts",
            "voices": f"{PUBLIC_BASE_URL}/api/voices",
            "quick_mp3": f"{PUBLIC_BASE_URL}/tts.mp3?q=Salom",
            "health": f"{PUBLIC_BASE_URL}/health",
        },
        "usage_example": {
            "curl": f'curl -X POST {PUBLIC_BASE_URL}/api/tts -H "Content-Type: application/json" -d \'{{"text":"Salom, dunyo!","voice":"uz-UZ-SardorNeural"}}\' -o output.mp3',
            "python": f'import requests; r = requests.post("{PUBLIC_BASE_URL}/api/tts", json={{"text": "Salom!", "voice": "uz-UZ-SardorNeural"}}); open("output.mp3", "wb").write(r.content)',
        },
    })


@app.route("/health")
@app.route("/ping")
def health():
    import bot
    return jsonify({
        "status": "healthy",
        "service": PROJECT_NAME,
        "version": PROJECT_VERSION,
        "uptime_seconds": int(time.time() - START),
        "bot_active": bot.ACTIVE,
        "app_url": PUBLIC_BASE_URL,
        "bot_url": BOT_URL,
        "github_url": GITHUB_URL,
    })


# ─── SEO & AI discovery files ───

@app.route("/robots.txt")
def robots_txt():
    return send_from_directory(BASE_DIR, "robots.txt", mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{PUBLIC_BASE_URL}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{PUBLIC_BASE_URL}/guide</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{PUBLIC_BASE_URL}/api/voices</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>
</urlset>"""
    return Response(content, mimetype="application/xml")


@app.route("/llms.txt")
def llms_txt():
    return send_from_directory(BASE_DIR, "llms.txt", mimetype="text/plain; charset=utf-8")


@app.route("/llms-full.txt")
def llms_full_txt():
    return send_from_directory(BASE_DIR, "llms-full.txt", mimetype="text/plain; charset=utf-8")


@app.route("/ai-plugin.json")
def ai_plugin():
    return jsonify({
        "schema_version": "v1",
        "name_for_human": PROJECT_NAME,
        "name_for_model": "uzbekcha_tts",
        "description_for_human": PROJECT_DESCRIPTION,
        "description_for_model": "Converts Uzbek text to natural speech (MP3 audio). Supports Uzbek, Russian, English, Turkish, and Kazakh voices. Use GET /tts.mp3?q=TEXT or POST /api/tts with JSON body {\"text\": \"...\", \"voice\": \"uz-UZ-SardorNeural\"}. Returns audio/mpeg binary.",
        "auth": {"type": "none"},
        "api": {
            "type": "openapi",
            "url": f"{PUBLIC_BASE_URL}/openapi.yaml",
        },
        "logo_url": f"{PUBLIC_BASE_URL}/static/icon-512.png",
        "contact_email": "",
        "legal_info_url": f"{PUBLIC_BASE_URL}/guide",
    })


@app.route("/openapi.yaml")
def openapi_yaml():
    return send_from_directory(BASE_DIR, "openapi.yaml", mimetype="text/yaml; charset=utf-8")


@app.route("/.well-known/ai-plugin.json")
def well_known_ai_plugin():
    return ai_plugin()


# ─── Static files ───

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


# ─── Main entry point ───

def main():
    print(f"🌟 {PROJECT_NAME} v{PROJECT_VERSION} | PORT {PORT} | {PUBLIC_BASE_URL} | bot: {BOT_URL}", flush=True)
    import bot
    if bot.TOKEN:
        threading.Thread(target=bot.run, daemon=True).start()
    else:
        print("ℹ️ BOT_TOKEN not found — running website and API only.", flush=True)
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
