"""
🚀 Universal AI Text-to-Speech Cloud Server (Flask + Telegram Bot)
- 100% Bepul va Cheksiz (Microsoft Edge Neural TTS)
- Render.com, Hugging Face, va GitHub uchun maxsus optimallashtirilgan
- Xatoliklarga chidamli (Fail-safe, Auto-reconnect, Health-check)
"""

import os
import io
import sys
import time
import asyncio
import threading
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import edge_tts
import telebot
from telebot import types

# Server va Muhit sozlamalari
BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"

app = Flask(__name__, static_folder=str(PUBLIC_DIR))
CORS(app)

PORT = int(os.environ.get("PORT", 5000))
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

START_TIME = time.time()
BOT_ACTIVE = False

# ============================================================
# 1. SARALANGAN OVOZLAR VA TTS YADROSI
# ============================================================

VOICES = [
    {
        "id": "uz-UZ-SardorNeural",
        "name": "Sardor (O'zbekcha)",
        "gender": "Erkak",
        "lang": "uz-UZ",
        "badge": "🇺🇿 Tavsiya etiladi",
        "desc": "Aniq, baquvvat va professional diktor ovozi"
    },
    {
        "id": "uz-UZ-MadinaNeural",
        "name": "Madina (O'zbekcha)",
        "gender": "Ayol",
        "lang": "uz-UZ",
        "badge": "🇺🇿 O'zbekcha",
        "desc": "Muloyim, yoqimli va tabiiy ayol ovozi"
    },
    {
        "id": "tr-TR-AhmetNeural",
        "name": "Ahmet (Turkcha)",
        "gender": "Erkak",
        "lang": "tr-TR",
        "badge": "🇹🇷 Turkcha",
        "desc": "Turkcha professional diktor ovozi"
    },
    {
        "id": "ru-RU-DmitryNeural",
        "name": "Dmitry (Ruscha)",
        "gender": "Erkak",
        "lang": "ru-RU",
        "badge": "🇷🇺 Ruscha",
        "desc": "Klassik professional diktor"
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (Inglizcha US)",
        "gender": "Erkak",
        "lang": "en-US",
        "badge": "🇺🇸 Inglizcha",
        "desc": "Dinamik, zamonaviy amerikacha ovoz"
    }
]

async def synthesize_with_retry(text: str, voice: str = "uz-UZ-SardorNeural", rate: str = "+0%", pitch: str = "+0Hz", volume: str = "+0%", max_retries: int = 3) -> io.BytesIO:
    """
    Matnni MP3 buferiga aylantiradi.
    Tarmoqda uzilish bo'lsa, avtomatik 3 marta qayta urinadi.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            audio_buffer.seek(0)
            
            if audio_buffer.getbuffer().nbytes > 0:
                return audio_buffer
            else:
                raise ValueError("Bo'sh audio buferi qaytdi")
        except Exception as e:
            last_error = e
            print(f"⚠️ TTS urinish {attempt+1}/{max_retries} xatosi: {e}", flush=True)
            await asyncio.sleep(1.0)

    raise Exception(f"TTS sintezi muvaffaqiyatsiz bo'ldi: {last_error}")

# ============================================================
# 2. VEB-SAYT VA API BOSHQARUVI (FLASK)
# ============================================================

@app.route("/")
def serve_index():
    """Bosh sahifani xavfsiz yuklash (har qanday papka tuzilishida ishlaydi)"""
    if (PUBLIC_DIR / "index.html").exists():
        return send_from_directory(str(PUBLIC_DIR), "index.html")
    elif (BASE_DIR / "index.html").exists():
        return send_from_directory(str(BASE_DIR), "index.html")
    elif (BASE_DIR / "templates" / "index.html").exists():
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
        "service": "AI TTS Universal Server"
    }), 200

@app.route("/api/voices", methods=["GET"])
def api_voices():
    """Mavjud ovozlar ro'yxatini qaytarish"""
    return jsonify({
        "status": "success",
        "voices": VOICES
    })

@app.route("/api/tts", methods=["POST"])
def api_tts():
    """Veb-saytdan kelgan matnni MP3 audio qilib qaytarish"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        text = str(data.get("text", "")).strip()
        
        if not text:
            return jsonify({"status": "error", "message": "Iltimos, matn kiriting!"}), 400

        # Xavfsizlik: juda katta matnlarni cheklash (5000 belgi)
        if len(text) > 5000:
            return jsonify({
                "status": "error", 
                "message": "Matn juda uzun! Maksimal 5000 belgi yuboring."
            }), 400

        voice = str(data.get("voice", "uz-UZ-SardorNeural"))
        rate = str(data.get("rate", "+0%"))
        pitch = str(data.get("pitch", "+0Hz"))
        volume = str(data.get("volume", "+0%"))

        # Parametrlarni to'g'ri formatga keltirish
        if not (rate.startswith("+") or rate.startswith("-")):
            rate = f"+{rate}" if not rate.endswith("%") else rate
        if not rate.endswith("%"):
            rate = f"{rate}%"

        if not (pitch.startswith("+") or pitch.startswith("-")):
            pitch = f"+{pitch}"
        if not pitch.endswith("Hz"):
            pitch = f"{pitch}Hz"

        if not (volume.startswith("+") or volume.startswith("-")):
            volume = f"+{volume}"
        if not volume.endswith("%"):
            volume = f"{volume}%"

        # Audio sintezi
        audio_buffer = asyncio.run(synthesize_with_retry(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        ))

        return send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name=f"ovoz_{int(time.time())}.mp3"
        )
    except Exception as e:
        print(f"❌ API Xatolik: {e}", flush=True)
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================
# 3. TELEGRAM BOT (XATOLIKLARGA CHIDAMLI FON OQIMI)
# ============================================================

USER_TG_SETTINGS = {}

def start_telegram_bot_thread():
    """Telegram Botni xavfsiz va uzluksiz rejimda ishga tushirish"""
    global BOT_ACTIVE
    
    if not BOT_TOKEN or BOT_TOKEN in ["SIZNING_BOT_TOKENINGIZ", "YOUR_BOT_TOKEN", ""]:
        print("ℹ️ [INFO] BOT_TOKEN belgilanmagan. Faqat Veb-sayt ishlamoqda.", flush=True)
        print("💡 [MASLAHAT] Botni yoqish uchun Render Environment Variables'ga BOT_TOKEN qo'shing.", flush=True)
        return

    print("🤖 Telegram Bot ulanmoqda...", flush=True)
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

    VOICE_KEYBOARD = types.InlineKeyboardMarkup(row_width=2)
    VOICE_KEYBOARD.add(
        types.InlineKeyboardButton("🇺🇿 Sardor (Erkak)", callback_data="set_uz-UZ-SardorNeural"),
        types.InlineKeyboardButton("🇺🇿 Madina (Ayol)", callback_data="set_uz-UZ-MadinaNeural"),
        types.InlineKeyboardButton("🇹🇷 Ahmet (Turkcha)", callback_data="set_tr-TR-AhmetNeural"),
        types.InlineKeyboardButton("🇷🇺 Dmitry (Ruscha)", callback_data="set_ru-RU-DmitryNeural"),
        types.InlineKeyboardButton("🇺🇸 Guy (Inglizcha)", callback_data="set_en-US-GuyNeural")
    )

    @bot.message_handler(commands=['start', 'help'])
    def welcome(msg):
        uid = msg.from_user.id
        if uid not in USER_TG_SETTINGS:
            USER_TG_SETTINGS[uid] = "uz-UZ-SardorNeural"
        
        bot.reply_to(
            msg,
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Men matnlarni <b>professional sun'iy intellekt ovoziga (Voice)</b> aylantirib beruvchi bepul botman.\n\n"
            "✍️ Menga istalgan matn yuboring, darhol ovoz qilib beraman!\n\n"
            "🎙️ Ovozni o'zgartirish uchun quyidagi tugmalardan birini tanlang:",
            reply_markup=VOICE_KEYBOARD
        )

    @bot.message_handler(commands=['voice'])
    def change_voice(msg):
        bot.reply_to(msg, "🎙️ <b>Kerakli ovozni tanlang:</b>", reply_markup=VOICE_KEYBOARD)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("set_"))
    def on_voice_select(call):
        chosen_voice = call.data.replace("set_", "")
        USER_TG_SETTINGS[call.from_user.id] = chosen_voice
        bot.answer_callback_query(call.id, "Ovoz saqlandi! ✅")
        bot.send_message(
            call.message.chat.id,
            f"✅ Ovoz o'rnatildi: <b>{chosen_voice}</b>\n\nEndi matningizni yuborishingiz mumkin:"
        )

    @bot.message_handler(content_types=['text'])
    def on_user_text(msg):
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
                rate="+10%"
            ))
            audio_buffer.name = "voice.ogg"
            bot.send_voice(
                chat_id=msg.chat.id,
                voice=audio_buffer,
                reply_to_message_id=msg.message_id
            )
        except Exception as e:
            bot.reply_to(msg, f"❌ Ovoz yaratishda xatolik: {str(e)}")

    # Uzluksiz qayta ulanish zanjiri (Auto-reconnect)
    while True:
        try:
            BOT_ACTIVE = True
            print("✅ Telegram Bot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda!", flush=True)
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as err:
            BOT_ACTIVE = False
            print(f"⚠️ Telegram bot tarmoq xatosi: {err}. 5 soniyadan so'ng qayta ulanadi...", flush=True)
            time.sleep(5)

# ============================================================
# 4. SERVERNI ISHGA TUSHIRISH
# ============================================================

def main():
    print("=" * 60, flush=True)
    print("🌟 AI VOICE STUDIO (WEB + TELEGRAM BOT)", flush=True)
    print(f"📍 HOST: 0.0.0.0 | PORT: {PORT}", flush=True)
    print("=" * 60, flush=True)

    # Telegram botni fondagi alohida oqimda yoqish
    if BOT_TOKEN:
        bot_thread = threading.Thread(target=start_telegram_bot_thread, daemon=True)
        bot_thread.start()
    else:
        print("ℹ️ BOT_TOKEN topilmadi (faqat veb-sayt ishga tushmoqda).", flush=True)

    # Flask veb serverini yoqish
    app.run(host="0.0.0.0", port=PORT, debug=False)

if __name__ == "__main__":
    main()
