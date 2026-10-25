"""
Infinite AI Text-to-Speech server with web UI + Telegram bot.
- Uses Microsoft Edge Neural TTS
- Includes API and optional Telegram channel subscription gate
- Supports multiple styles and custom output filename
"""

import os
import re
import io
import time
import asyncio
import threading
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import edge_tts
import telebot
from telebot import types

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"

app = Flask(__name__, static_folder=str(PUBLIC_DIR))
CORS(app)

PORT = int(os.environ.get("PORT", 5000))
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
START_TIME = time.time()
BOT_ACTIVE = False

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://tts-uzbek.onrender.com").strip().rstrip("/")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Uzbekcha_tts_bot").strip().lstrip("@")
BOT_LINK = f"https://t.me/{BOT_USERNAME}" if BOT_USERNAME else "https://t.me/Uzbekcha_tts_bot"

DEFAULT_AUDIO_FILENAME = os.environ.get("DEFAULT_AUDIO_FILENAME", "tts_audio").strip() or "tts_audio"
SUBSCRIBE_REQUIRED = str(os.environ.get("SUBSCRIBE_REQUIRED", "true")).strip().lower() in {"1", "true", "yes", "on"}
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "@tgchannel").strip()

VOICES = [
    {"id": "uz-UZ-SardorNeural", "name": "Sardor (O'zbekcha)", "gender": "Erkak", "lang": "uz-UZ", "badge": "🇺🇿", "desc": "Aniq va professional ovoz"},
    {"id": "uz-UZ-MadinaNeural", "name": "Madina (O'zbekcha)", "gender": "Ayol", "lang": "uz-UZ", "badge": "🇺🇿", "desc": "Yumshoq va tabiiy ovoz"},
    {"id": "tr-TR-AhmetNeural", "name": "Ahmet (Turkcha)", "gender": "Erkak", "lang": "tr-TR", "badge": "🇹🇷", "desc": "Turkcha ovoz"},
    {"id": "ru-RU-DmitryNeural", "name": "Dmitry (Ruscha)", "gender": "Erkak", "lang": "ru-RU", "badge": "🇷🇺", "desc": "Klassik ovoz"},
    {"id": "en-US-AlexNeural", "name": "Alex (Inglizcha)", "gender": "Erkak", "lang": "en-US", "badge": "🇺🇸", "desc": "Zamonaviy va aniq ovoz"},
]

STYLE_PRESETS = [
    {"id": "robot", "name": "Robot", "rate": "+8%", "pitch": "+6Hz", "volume": "+3%"},
    {"id": "minion", "name": "Minion", "rate": "+18%", "pitch": "+10Hz", "volume": "+6%"},
    {"id": "narrator", "name": "Narrator", "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"},
    {"id": "dramatic", "name": "Dramatic", "rate": "+5%", "pitch": "+12Hz", "volume": "+10%"},
    {"id": "whisper", "name": "Whisper", "rate": "-10%", "pitch": "-5Hz", "volume": "-5%"},
    {"id": "cinematic", "name": "Cinematic", "rate": "+2%", "pitch": "+8Hz", "volume": "+8%"},
]


def normalize_rate(value, default="+0%"):
    val = str(value or default).strip()
    if not val:
        return default
    if not (val.startswith("+") or val.startswith("-")):
        val = f"+{val}"
    if not val.endswith("%"):
        val = f"{val}%"
    return val


def normalize_pitch(value, default="+0Hz"):
    val = str(value or default).strip()
    if not val:
        return default
    if not (val.startswith("+") or val.startswith("-")):
        val = f"+{val}"
    if not val.endswith("Hz"):
        val = f"{val}Hz"
    return val


def normalize_volume(value, default="+0%"):
    val = str(value or default).strip()
    if not val:
        return default
    if not (val.startswith("+") or val.startswith("-")):
        val = f"+{val}"
    if not val.endswith("%"):
        val = f"{val}%"
    return val


def sanitize_filename(raw_name, fallback=None):
    base = str(raw_name or fallback or DEFAULT_AUDIO_FILENAME).strip()
    cleaned = re.sub(r"[^A-Za-z0-9_\- ]+", "", base).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    if not cleaned:
        cleaned = str(fallback or DEFAULT_AUDIO_FILENAME).strip()
    return cleaned


def get_request_payload():
    payload = request.get_json(force=True, silent=True) or {}
    if isinstance(payload, dict):
        return payload
    merged = {}
    for key in ["text", "voice", "style", "rate", "pitch", "volume", "filename", "file_name"]:
        value = request.args.get(key)
        if value is not None:
            merged[key] = value
    return merged


async def synthesize_with_retry(
    text: str,
    voice: str = "uz-UZ-SardorNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
    style: str = "narrator",
    max_retries: int = 3,
) -> io.BytesIO:
    style_cfg = next((item for item in STYLE_PRESETS if item["id"] == str(style).lower()), STYLE_PRESETS[2])
    rate = normalize_rate(rate or style_cfg.get("rate", "+0%"))
    pitch = normalize_pitch(pitch or style_cfg.get("pitch", "+0Hz"))
    volume = normalize_volume(volume or style_cfg.get("volume", "+0%"))

    last_error = None
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume,
            )
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            buffer.seek(0)
            if buffer.getbuffer().nbytes > 0:
                return buffer
            raise ValueError("Bo'sh audio buferi qaytdi")
        except Exception as exc:
            last_error = exc
            print(f"⚠️ TTS urinish {attempt + 1}/{max_retries} xatosi: {exc}", flush=True)
            await asyncio.sleep(1.0)
    raise Exception(f"TTS sintezi muvaffaqiyatsiz bo'ldi: {last_error}")


@app.route("/")
def serve_index():
    if (PUBLIC_DIR / "index.html").exists():
        return send_from_directory(str(PUBLIC_DIR), "index.html")
    if (BASE_DIR / "index.html").exists():
        return send_from_directory(str(BASE_DIR), "index.html")
    if (BASE_DIR / "templates" / "index.html").exists():
        return send_from_directory(str(BASE_DIR / "templates"), "index.html")
    return "<h1>Infinite AI TTS</h1><p>index.html topilmadi.</p>", 404


@app.route("/health")
@app.route("/ping")
def health_check():
    uptime = int(time.time() - START_TIME)
    return jsonify({
        "status": "healthy",
        "uptime_seconds": uptime,
        "bot_active": BOT_ACTIVE,
        "service": "Infinite AI TTS",
        "app_url": PUBLIC_BASE_URL,
        "bot_url": BOT_LINK,
        "subscribe_required": SUBSCRIBE_REQUIRED,
        "telegram_channel": TELEGRAM_CHANNEL,
    }), 200


@app.route("/api/voices", methods=["GET"])
def api_voices():
    return jsonify({
        "status": "success",
        "app_url": PUBLIC_BASE_URL,
        "bot_url": BOT_LINK,
        "voices": VOICES,
        "styles": STYLE_PRESETS,
        "subscribe_required": SUBSCRIBE_REQUIRED,
        "telegram_channel": TELEGRAM_CHANNEL,
    })


@app.route("/api/tts", methods=["GET", "POST"])
@app.route("/api/tts/quick", methods=["GET", "POST"])
def api_tts():
    try:
        data = get_request_payload()
        text = str(data.get("text", "")).strip()
        if not text:
            return jsonify({"status": "error", "message": "Iltimos, matn kiriting!"}), 400
        if len(text) > 5000:
            return jsonify({"status": "error", "message": "Matn juda uzun! Maksimal 5000 belgi."}), 400

        voice = str(data.get("voice", "en-US-AlexNeural")).strip() or "en-US-AlexNeural"
        rate = normalize_rate(data.get("rate", "+0%"))
        pitch = normalize_pitch(data.get("pitch", "+0Hz"))
        volume = normalize_volume(data.get("volume", "+0%"))
        style = str(data.get("style", "narrator")).strip().lower() or "narrator"
        filename = sanitize_filename(data.get("filename") or data.get("file_name"), DEFAULT_AUDIO_FILENAME)

        audio_buffer = asyncio.run(synthesize_with_retry(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
            style=style,
        ))

        download_name = f"{filename}.mp3"
        return send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name=download_name,
        )
    except Exception as exc:
        print(f"❌ API Xatolik: {exc}", flush=True)
        return jsonify({"status": "error", "message": str(exc)}), 500


USER_TG_SETTINGS = {}


def get_channel_username(channel_value):
    if not channel_value:
        return ""
    value = str(channel_value).strip()
    if value.startswith("@"):
        return value
    if value.startswith("https://t.me/"):
        return "@" + value.split("/", 3)[-1].strip("/")
    if value.startswith("t.me/"):
        return "@" + value.replace("t.me/", "").strip("/")
    return "@" + value


def check_subscribed(bot_client, user_id, channel_value):
    if not SUBSCRIBE_REQUIRED or not channel_value:
        return True
    channel = get_channel_username(channel_value)
    try:
        member = bot_client.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in {"member", "administrator", "creator"}
    except Exception:
        return False


def start_telegram_bot_thread():
    global BOT_ACTIVE
    if not BOT_TOKEN or BOT_TOKEN in {"YOUR_BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ", ""}:
        print("ℹ️ BOT_TOKEN topilmadi. Faqat veb-sayt ishlaydi.", flush=True)
        return

    print("🤖 Telegram bot ulanmoqda...", flush=True)
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

    voice_keyboard = types.InlineKeyboardMarkup(row_width=2)
    voice_keyboard.add(
        types.InlineKeyboardButton("🇺🇿 Sardor", callback_data="set_uz-UZ-SardorNeural"),
        types.InlineKeyboardButton("🇺🇿 Madina", callback_data="set_uz-UZ-MadinaNeural"),
        types.InlineKeyboardButton("🇹🇷 Ahmet", callback_data="set_tr-TR-AhmetNeural"),
        types.InlineKeyboardButton("🇷🇺 Dmitry", callback_data="set_ru-RU-DmitryNeural"),
        types.InlineKeyboardButton("🇺🇸 Alex", callback_data="set_en-US-AlexNeural"),
    )

    @bot.message_handler(commands=["start", "help"])
    def welcome(msg):
        uid = msg.from_user.id
        if uid not in USER_TG_SETTINGS:
            USER_TG_SETTINGS[uid] = "uz-UZ-SardorNeural"

        if SUBSCRIBE_REQUIRED and TELEGRAM_CHANNEL and not check_subscribed(bot, uid, TELEGRAM_CHANNEL):
            channel = get_channel_username(TELEGRAM_CHANNEL)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📣 Kanalga o'tish", url=f"https://t.me/{channel.lstrip('@')}"))
            bot.reply_to(
                msg,
                f"📣 Botdan foydalanish uchun avval <b>{channel}</b> kanaliga obuna bo'ling.\n\nObunani bajargach /start ni qayta yuboring.",
                reply_markup=markup,
            )
            return

        bot.reply_to(
            msg,
            "�� <b>Assalomu alaykum!</b>\n\n"
            "Men matnlarni professional sun'iy intellekt ovoziga aylantirib beraman.\n\n"
            f"🌐 Sayt: <a href='{PUBLIC_BASE_URL}'>{PUBLIC_BASE_URL}</a>\n"
            f"🤖 Bot: <a href='{BOT_LINK}'>{BOT_LINK}</a>\n\n"
            "✍️ Menga istalgan matn yuboring.\n\n"
            "🎙️ Ovozni o'zgartirish uchun /voice buyrug'ini bering.",
            reply_markup=voice_keyboard,
        )

    @bot.message_handler(commands=["voice"])
    def change_voice(msg):
        if SUBSCRIBE_REQUIRED and TELEGRAM_CHANNEL and not check_subscribed(bot, msg.from_user.id, TELEGRAM_CHANNEL):
            channel = get_channel_username(TELEGRAM_CHANNEL)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📣 Kanalga o'tish", url=f"https://t.me/{channel.lstrip('@')}"))
            bot.reply_to(msg, f"📣 Botdan foydalanish uchun avval <b>{channel}</b> kanaliga obuna bo'ling.", reply_markup=markup)
            return
        bot.reply_to(msg, "🎙️ Kerakli ovozni tanlang:", reply_markup=voice_keyboard)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("set_"))
    def on_voice_select(call):
        chosen_voice = call.data.replace("set_", "")
        USER_TG_SETTINGS[call.from_user.id] = chosen_voice
        bot.answer_callback_query(call.id, "Ovoz saqlandi! ✅")
        bot.send_message(call.message.chat.id, f"✅ Ovoz o'rnatildi: <b>{chosen_voice}</b>\n\nEndi matningizni yuborishingiz mumkin:")

    @bot.message_handler(content_types=["text"])
    def on_user_text(msg):
        if SUBSCRIBE_REQUIRED and TELEGRAM_CHANNEL and not check_subscribed(bot, msg.from_user.id, TELEGRAM_CHANNEL):
            channel = get_channel_username(TELEGRAM_CHANNEL)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📣 Kanalga o'tish", url=f"https://t.me/{channel.lstrip('@')}"))
            bot.reply_to(msg, f"📣 Botdan foydalanish uchun avval <b>{channel}</b> kanaliga obuna bo'ling.", reply_markup=markup)
            return

        text = msg.text.strip()
        if not text:
            return
        if len(text) > 4000:
            bot.reply_to(msg, "⚠️ Matn juda uzun. Iltimos, 4000 belgidan kamroq matn yuboring.")
            return

        voice = USER_TG_SETTINGS.get(msg.from_user.id, "uz-UZ-SardorNeural")
        bot.send_chat_action(msg.chat.id, "record_audio")
        try:
            audio_buffer = asyncio.run(synthesize_with_retry(
                text=text,
                voice=voice,
                rate="+10%",
                pitch="+0Hz",
                volume="+0%",
                style="narrator",
            ))
            audio_buffer.name = "voice.ogg"
            bot.send_voice(chat_id=msg.chat.id, voice=audio_buffer, reply_to_message_id=msg.message_id)
        except Exception as exc:
            bot.reply_to(msg, f"❌ Ovoz yaratishda xatolik: {exc}")

    while True:
        try:
            BOT_ACTIVE = True
            print("✅ Telegram bot muvaffaqiyatli ishga tushdi.", flush=True)
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as err:
            BOT_ACTIVE = False
            print(f"⚠️ Telegram botda tarmoq xatosi: {err}. 5 soniyadan so'ng qayta ulanadi...", flush=True)
            time.sleep(5)


def main():
    print("=" * 60, flush=True)
    print("🌟 Infinite AI TTS (WEB + TELEGRAM BOT)", flush=True)
    print(f"📍 HOST: 0.0.0.0 | PORT: {PORT}", flush=True)
    print(f"🌐 APP URL: {PUBLIC_BASE_URL}", flush=True)
    print(f"🤖 BOT URL: {BOT_LINK}", flush=True)
    print(f"📣 SUBSCRIBE_REQUIRED: {SUBSCRIBE_REQUIRED} | TELEGRAM_CHANNEL: {TELEGRAM_CHANNEL or 'not set'}", flush=True)
    print("=" * 60, flush=True)

    if BOT_TOKEN:
        bot_thread = threading.Thread(target=start_telegram_bot_thread, daemon=True)
        bot_thread.start()
    else:
        print("ℹ️ BOT_TOKEN topilmadi. Faqat veb-sayt ishlaydi.", flush=True)

    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    main()
