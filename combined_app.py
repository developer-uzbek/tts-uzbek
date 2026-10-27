"""VoiceCraft Pro: veb-sayt + cheksiz TTS API (?q= / ?r=) + Telegram bot — bitta jarayonda."""
import io
import hmac
import os
import re
import time
import threading
from collections import deque
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

import core

BASE_DIR = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", 5000))
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://tts-uzbek.onrender.com").strip().rstrip("/")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Uzbekcha_tts_bot").strip().lstrip("@")
BOT_URL = f"https://t.me/{BOT_USERNAME}"
RATE_PER_MIN = int(os.environ.get("RATE_PER_MIN", 40))  # bitta IP uchun keshda yo'q so'rovlar/daqiqa; 0 = cheklovsiz
DEFAULT_NAME = os.environ.get("DEFAULT_AUDIO_FILENAME", "tts_audio").strip() or "tts_audio"
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
        raise core.Busy(f"Juda tez! Daqiqada {RATE_PER_MIN} tadan ortiq yangi matn yuborib bo'lmaydi. Biroz kuting.")
    q.append(now)
    if len(_hits) > 5000:  # xotirani tozalash
        for k in [k for k, v in _hits.items() if not v or v[-1] < now - 60]:
            _hits.pop(k, None)


def client_ip():
    return (request.headers.get("CF-Connecting-IP")
            or request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip())


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
        return fail("Matn kiriting. Masalan: /?q=Salom", 400)
    if len(text) > core.MAX_CHARS:
        return fail(f"Matn juda uzun: {len(text)} belgi (bitta so'rovda maksimal {core.MAX_CHARS}). Matnni bo'lib yuboring.", 413)
    try:
        o = core.opts(d)
        sig = str(d.get("sig") or "")  # bot imzolagan inline havola: Telegram serverlari umumiy IP limitiga tushmasin
        trusted = bool(sig) and hmac.compare_digest(sig, core.sign(text, o["voice"]))
        data = core.synth(text, o, on_miss=None if trusted else (lambda: check_rate(client_ip())))
    except core.Busy as exc:
        r = jsonify({"status": "error", "message": str(exc)})
        r.status_code, r.headers["Retry-After"] = 429, "10"
        return r
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        print(f"❌ TTS xatosi: {exc}", flush=True)
        return fail(str(exc), 502)
    name = re.sub(r"[^A-Za-z0-9_\- ]+", "", str(d.get("filename") or d.get("name") or "")).strip().replace(" ", "_") or DEFAULT_NAME
    dl = str(d.get("dl", "")).lower() in {"1", "true", "yes"}
    return send_file(io.BytesIO(data), mimetype="audio/mpeg", as_attachment=dl,
                     download_name=f"{name}.mp3", conditional=True, max_age=86400)


@app.route("/")
def index():
    if "q" in request.args or "r" in request.args:  # /?q=salom  yoki  /?r=salom  -> to'g'ridan-to'g'ri MP3
        return tts_response(request.args.to_dict())
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/tts.mp3")
def mp3():  # /tts.mp3?q=Salom — kengaytmali havola (Telegram inline va <audio> uchun qulay)
    return tts_response(request.args.to_dict())


@app.route("/tts.py")
def cli_script():
    return send_from_directory(BASE_DIR, "tts.py", mimetype="text/plain; charset=utf-8")


@app.route("/api/tts", methods=["GET", "POST"])
@app.route("/api/tts/quick", methods=["GET", "POST"])
def api_tts():
    return tts_response(payload())


@app.route("/api/voices")
def api_voices():
    return jsonify({"status": "success", "app_url": PUBLIC_BASE_URL, "bot_url": BOT_URL, "max_chars": core.MAX_CHARS,
                    "voices": core.voices(),
                    "styles": [{"id": k, "name": v[0]} for k, v in core.STYLES.items()]})


@app.route("/health")
@app.route("/ping")
def health():
    import bot
    return jsonify({"status": "healthy", "uptime_seconds": int(time.time() - START), "bot_active": bot.ACTIVE,
                    "app_url": PUBLIC_BASE_URL, "bot_url": BOT_URL})


def main():
    print(f"🌟 VoiceCraft Pro | PORT {PORT} | {PUBLIC_BASE_URL} | bot: {BOT_URL}", flush=True)
    import bot
    if bot.TOKEN:
        threading.Thread(target=bot.run, daemon=True).start()
    else:
        print("ℹ️ BOT_TOKEN topilmadi — faqat sayt va API ishlaydi.", flush=True)
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
