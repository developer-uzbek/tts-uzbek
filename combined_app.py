"""
🚀 Universal AI Text-to-Speech Cloud Server (Flask + Telegram Bot)
- 100% Bepul va Cheksiz (Microsoft Edge Neural TTS)
- Render.com, Hugging Face, va GitHub uchun maxsus optimallashtirilgan
- Xatoliklarga chidamli (Fail-safe, Auto-reconnect, Health-check)
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

DEFAULT_FILENAME_PREFIX = os.environ.get("DEFAULT_AUDIO_FILENAME", "tts_audio").strip() or "tts_audio"
SUBSCRIBE_REQUIRED = str(os.environ.get("SUBSCRIBE_REQUIRED", "false")).strip().lower() in {
    "1", "true", "yes", "on"
}
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "").strip()


def env_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


VOICES = [
    {
        "id": "uz-UZ-SardorNeural",
        "name": "Sardor (O'zbekcha)",
        "gender": "Erkak",
        "lang": "uz-UZ",
        "badge": "🇺🇿 Tavsiya etiladi",
        "desc": "Aniq, baquvvat va professional diktor ovozi",
    },
    {
        "id": "uz-UZ-MadinaNeural",
        "name": "Madina (O'zbekcha)",
        "gender": "Ayol",
        "lang": "uz-UZ",
        "badge": "🇺🇿 O'zbekcha",
        "desc": "Muloyim, yoqimli va tabiiy ayol ovozi",
    },
    {
        "id": "tr-TR-AhmetNeural",
        "name": "Ahmet (Turkcha)",
        "gender": "Erkak",
        "lang": "tr-TR",
        "badge": "🇹🇷 Turkcha",
        "desc": "Turkcha professional diktor ovozi",
    },
    {
        "id": "ru-RU-DmitryNeural",
        "name": "Dmitry (Ruscha)",
        "gender": "Erkak",
        "lang": "ru-RU",
        "badge": "🇷🇺 Ruscha",
        "desc": "Klassik professional diktor",
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (Inglizcha US)",
        "gender": "Erkak",
        "lang": "en-US",
        "badge": "🇺🇸 Inglizcha",
        "desc": "Dinamik, zamonaviy amerikacha ovoz",
    },
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
        val = default
    if not (val.startswith("+") or val.startswith("-")):
        val = f"+{val}"
    if not val.endswith("%"):
        val = f"{val}%"
    return val


def normalize_pitch(value, default="+0Hz"):
    val = str(value or default).strip()
    if not val:
        val = default
    if not (val.startswith("+") or val.startswith("-")):
        val = f"+{val}"
    if not val.endswith("Hz"):
        val = f"{val}Hz"
    return val


def normalize_volume(value, default="+0%"):
    val = str(value or default).strip()
    if not val:
        val = default
    if not (val.startswith("+") or val.startswith("-")):
        val = f"+{val}"
    if not val.endswith("%"):
        val = f"{val}%"
    return val


def sanitize_filename(raw_name, fallback=None):
    base = str(raw_name or fallback or DEFAULT_FILENAME_PREFIX).strip()
    cleaned = re.sub(r"[^A-Za-z0-9_\- ]+", "", base).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    if not cleaned:
        cleaned = str(fallback or DEFAULT_FILENAME_PREFIX).strip()
    return cleaned


async def synthesize_with_retry(
    text: str,
    voice: str = "uz-UZ-SardorNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
    style: str = "narrator",
    max_retries: int = 3,
) -> io.BytesIO:
    """Matnni MP3 buferiga aylantiradi. Tarmoqda uzilish bo'lsa avtomatik qayta urinadi."""
    style_cfg = next((item for item in STYLE_PRESETS if item["id"] == style.lower()), STYLE_PRESETS[0])
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
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])

            audio_buffer.seek(0)
            if audio_buffer.getbuffer().nbytes > 0:
                return audio_buffer
            raise ValueError("Bo'sh audio buferi qaytdi")
        except Exception as exc:  # pragma: no cover - runtime safety
            last_error = exc
            print(f"⚠️ TTS urinish {attempt + 1}/{max_retries} xatosi: {exc}", flush=True)
            await asyncio.sleep(1.0)

    raise Exception(f"TTS sintezi muvaffaqiyatsiz bo'ldi: {last_error}")


@app.route("/")
def serve_index():
    """Bosh sahifani xavfsiz yuklash (har qanday papka tuzilishida ishlaydi)"""
    if (PUBLIC_DIR / "index.html").exists():
        return send_from_directory(str(PUBLIC_DIR), "index.html")
    if (BASE_DIR / "index.html").exists():
        return send_from_directory(str(BASE_DIR), "index.html")
    if (BASE_DIR / "templates" / "index.html").exists():
        return send_from_directory(str(BASE_DIR / "templates"), "index.html")
    return "<h1>AI Voice Studio</h1><p>index.html fayli topilmadi.</p>", 404


@app.route("/health")
@app.route("/ping")
def health_check():
    """Render.com va Uptime monitoring uchun sog'lomlik tekshiruvi"""
    uptime = int(time.time() - START_TIME)
    return jsonify({
        "status": "healthy",
        "uptime_seconds": uptime,
        "bot_active": BOT_ACTIVE,
        "service": "AI TTS Universal Server",
        "subscribe_required": SUBSCRIBE_REQUIRED,
        "telegram_channel": TELEGRAM_CHANNEL,
    }), 200


@app.route("/api/voices", methods=["GET"])
def api_voices():
    """Mavjud ovozlar va uslublar ro'yxatini qaytarish"""
    return jsonify({
        "status": "success",
        "voices": VOICES,
        "styles": STYLE_PRESETS,
        "subscribe_required": SUBSCRIBE_REQUIRED,
        "telegram_channel": TELEGRAM_CHANNEL,
    })


@app.route("/api/tts", methods=["POST"])
def api_tts():
    """Veb-saytdan kelgan matnni MP3 audio qilib qaytarish"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        text = str(data.get("text", "")).strip()

        if not text:
            return jsonify({"status": "error", "message": "Iltimos, matn kiriting!"}), 400

        if len(text) > 5000:
            return jsonify({
                "status": "error",
                "message": "Matn juda uzun! Maksimal 5000 belgi yuboring.",
            }), 400

        voice = str(data.get("voice", "uz-UZ-SardorNeural")).strip() or "uz-UZ-SardorNeural"
        rate = normalize_rate(data.get("rate", "+0%"))
        pitch = normalize_pitch(data.get("pitch", "+0Hz"))
        volume = normalize_volume(data.get("volume", "+0%"))
        style = str(data.get("style", "narrator")).strip().lower() or "narrator"
        filename = sanitize_filename(data.get("filename") or data.get("file_name"), DEFAULT_FILENAME_PREFIX)

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
    except Exception as exc:  # pragma: no cover - runtime safety
        print(f"⚠️ Kanal obunasini tekshirishda xatolik: {exc}", flush=True)
        return False


def start_telegram_bot_thread():
    """Telegram Botni xavfsiz va uzluksiz rejimda ishga tushirish"""
    global BOT_ACTIVE

    if not BOT_TOKEN or BOT_TOKEN in {"SIZNING_BOT_TOKENINGIZ", "YOUR_BOT_TOKEN", ""}:
        print("ℹ️ [INFO] BOT_TOKEN belgilanmagan. Faqat Veb-sayt ishlamoqda.", flush=True)
        print("💡 [MASLAHAT] Botni yoqish uchun Render Environment Variables'ga BOT_TOKEN qo'shing.", flush=True)
        return

    print("🤖 Telegram Bot ulanmoqda...", flush=True)
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

    voice_keyboard = types.InlineKeyboardMarkup(row_width=2)
    voice_keyboard.add(
        types.InlineKeyboardButton("🇺🇿 Sardor (Erkak)", callback_data="set_uz-UZ-SardorNeural"),
        types.InlineKeyboardButton("🇺🇿 Madina (Ayol)", callback_data="set_uz-UZ-MadinaNeural"),
        types.InlineKeyboardButton("🇹🇷 Ahmet (Turkcha)", callback_data="set_tr-TR-AhmetNeural"),
        types.InlineKeyboardButton("🇷🇺 Dmitry (Ruscha)", callback_data="set_ru-RU-DmitryNeural"),
        types.InlineKeyboardButton("🇺🇸 Guy (Inglizcha)", callback_data="set_en-US-GuyNeural"),
    )

    @bot.message_handler(commands=["start", "help"])
    def welcome(msg):
        uid = msg.from_user.id
        if uid not in USER_TG_SETTINGS:
            USER_TG_SETTINGS[uid] = "uz-UZ-SardorNeural"

        if SUBSCRIBE_REQUIRED and TELEGRAM_CHANNEL:
            channel = get_channel_username(TELEGRAM_CHANNEL)
            if not check_subscribed(bot, uid, TELEGRAM_CHANNEL):
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("📣 Kanalga o'tish", url=f"https://t.me/{channel.lstrip('@')}"))
                bot.reply_to(
                    msg,
                    f"📣 Botdan foydalanish uchun avval <b>{channel}</b> kanaliga obuna bo'ling."
                    "\n\nObunani bajargach, /start buyrug'ini qayta yuboring.",
                    reply_markup=markup,
                )
                return

        bot.reply_to(
            msg,
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Men matnlarni <b>professional sun'iy intellekt ovoziga (Voice)</b> aylantirib beruvchi bepul botman.\n\n"
            "✍️ Menga istalgan matn yuboring, darhol ovoz qilib beraman!\n\n"
            "🎙️ Ovozni o'zgartirish uchun quyidagi tugmalardan birini tanlang:",
            reply_markup=voice_keyboard,
        )

    @bot.message_handler(commands=["voice"])
    def change_voice(msg):
        if SUBSCRIBE_REQUIRED and TELEGRAM_CHANNEL and not check_subscribed(bot, msg.from_user.id, TELEGRAM_CHANNEL):
            channel = get_channel_username(TELEGRAM_CHANNEL)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📣 Kanalga o'tish", url=f"https://t.me/{channel.lstrip('@')}"))
            bot.reply_to(
                msg,
                f"📣 Botdan foydalanish uchun avval <b>{channel}</b> kanaliga obuna bo'ling.",
                reply_markup=markup,
            )
            return
        bot.reply_to(msg, "🎙️ <b>Kerakli ovozni tanlang:</b>", reply_markup=voice_keyboard)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("set_"))
    def on_voice_select(call):
        chosen_voice = call.data.replace("set_", "")
        USER_TG_SETTINGS[call.from_user.id] = chosen_voice
        bot.answer_callback_query(call.id, "Ovoz saqlandi! ✅")
        bot.send_message(
            call.message.chat.id,
            f"✅ Ovoz o'rnatildi: <b>{chosen_voice}</b>\n\nEndi matningizni yuborishingiz mumkin:",
        )

    @bot.message_handler(content_types=["text"])
    def on_user_text(msg):
        if SUBSCRIBE_REQUIRED and TELEGRAM_CHANNEL and not check_subscribed(bot, msg.from_user.id, TELEGRAM_CHANNEL):
            channel = get_channel_username(TELEGRAM_CHANNEL)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📣 Kanalga o'tish", url=f"https://t.me/{channel.lstrip('@')}"))
            bot.reply_to(
                msg,
                f"📣 Botdan foydalanish uchun avval <b>{channel}</b> kanaliga obuna bo'ling.",
                reply_markup=markup,
            )
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
            bot.send_voice(
                chat_id=msg.chat.id,
                voice=audio_buffer,
                reply_to_message_id=msg.message_id,
            )
        except Exception as exc:
            bot.reply_to(msg, f"❌ Ovoz yaratishda xatolik: {exc}")

    while True:
        try:
            BOT_ACTIVE = True
            print("✅ Telegram Bot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda!", flush=True)
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as err:
            BOT_ACTIVE = False
            print(f"⚠️ Telegram bot tarmoq xatosi: {err}. 5 soniyadan so'ng qayta ulanadi...", flush=True)
            time.sleep(5)


def main():
    print("=" * 60, flush=True)
    print("🌟 AI VOICE STUDIO (WEB + TELEGRAM BOT)", flush=True)
    print(f"📍 HOST: 0.0.0.0 | PORT: {PORT}", flush=True)
    print(f"📣 SUBSCRIBE_REQUIRED: {SUBSCRIBE_REQUIRED} | CHANNEL: {TELEGRAM_CHANNEL or 'not set'}", flush=True)
    print("=" * 60, flush=True)

    if BOT_TOKEN:
        bot_thread = threading.Thread(target=start_telegram_bot_thread, daemon=True)
        bot_thread.start()
    else:
        print("ℹ️ BOT_TOKEN topilmadi (faqat veb-sayt ishga tushmoqda).", flush=True)

    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    main()
