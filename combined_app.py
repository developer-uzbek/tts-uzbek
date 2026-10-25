"""
Universal Runner: Sayt (Flask) + Telegram Bot (birgalikda 1 ta xostingda)
Hugging Face Spaces yoki Render.com uchun ideal.
"""

import os
import io
import asyncio
import threading
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import edge_tts
import telebot
from telebot import types

# Flask Ilovasi
app = Flask(__name__, static_folder="public")
CORS(app)

PORT = int(os.environ.get("PORT", 7860))  # Hugging Face: 7860, Render: $PORT
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

# ============================================================
# 1. TTS Dvigateli
# ============================================================
VOICES = [
    {"id": "uz-UZ-SardorNeural", "name": "Sardor (O'zbekcha)", "gender": "Erkak", "badge": "🇺🇿 Tavsiya etiladi"},
    {"id": "uz-UZ-MadinaNeural", "name": "Madina (O'zbekcha)", "gender": "Ayol", "badge": "🇺🇿 O'zbekcha"},
    {"id": "tr-TR-AhmetNeural", "name": "Ahmet (Turkcha)", "gender": "Erkak", "badge": "🇹🇷 Turkcha"},
    {"id": "ru-RU-DmitryNeural", "name": "Dmitry (Ruscha)", "gender": "Erkak", "badge": "🇷🇺 Ruscha"},
    {"id": "en-US-GuyNeural", "name": "Guy (Inglizcha US)", "gender": "Erkak", "badge": "🇺🇸 Inglizcha"}
]

async def synthesize_speech(text: str, voice: str = "uz-UZ-SardorNeural", rate: str = "+0%") -> io.BytesIO:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf

# ============================================================
# 2. Veb Sayt Marshrutlari (Flask)
# ============================================================
@app.route("/")
def home():
    return send_from_directory("public", "index.html")

@app.route("/api/voices")
def get_voices():
    return jsonify({"status": "success", "voices": VOICES})

@app.route("/api/tts", methods=["POST"])
def web_tts():
    try:
        data = request.get_json(force=True)
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"status": "error", "message": "Matn kiritilmadi"}), 400
        
        voice = data.get("voice", "uz-UZ-SardorNeural")
        rate = data.get("rate", "+0%")
        audio_buffer = asyncio.run(synthesize_speech(text, voice, rate))
        
        return send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="ovoz_ai.mp3"
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================
# 3. Telegram Bot (Fondagi Oqim)
# ============================================================
USER_VOICES = {}

def run_telegram_bot():
    if not BOT_TOKEN or BOT_TOKEN == "SIZNING_BOT_TOKENINGIZ":
        print("⚠️ BOT_TOKEN belgilanmagan. Faqat veb-sayt ishlamoqda.")
        return

    print("🤖 Telegram Bot ishga tushirilmoqda...")
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

    @bot.message_handler(commands=['start', 'help'])
    def welcome(msg):
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🇺🇿 Sardor", callback_data="set_uz-UZ-SardorNeural"),
            types.InlineKeyboardButton("🇺🇿 Madina", callback_data="set_uz-UZ-MadinaNeural"),
            types.InlineKeyboardButton("🇷🇺 Dmitry", callback_data="set_ru-RU-DmitryNeural"),
            types.InlineKeyboardButton("🇺🇸 Guy", callback_data="set_en-US-GuyNeural")
        )
        bot.reply_to(
            msg,
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Menga matn yuboring, men uni sun'iy intellekt ovoziga aylantirib beraman!\n\n"
            "🎙️ Ovozni tanlash uchun quyidagi tugmalardan birini bosing:",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("set_"))
    def on_voice_select(c):
        v = c.data.replace("set_", "")
        USER_VOICES[c.from_user.id] = v
        bot.answer_callback_query(c.id, "Ovoz saqlandi!")
        bot.send_message(c.message.chat.id, f"✅ Ovoz tanlandi: <b>{v}</b>\nMatningizni yuboring:")

    @bot.message_handler(content_types=['text'])
    def on_text(msg):
        text = msg.text.strip()
        if not text:
            return
        voice = USER_VOICES.get(msg.from_user.id, "uz-UZ-SardorNeural")
        bot.send_chat_action(msg.chat.id, "record_audio")
        try:
            buf = asyncio.run(synthesize_speech(text, voice=voice, rate="+10%"))
            buf.name = "voice.ogg"
            bot.send_voice(msg.chat.id, voice=buf, reply_to_message_id=msg.message_id)
        except Exception as e:
            bot.reply_to(msg, f"❌ Xatolik: {e}")

    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Bot xatosi: {e}")

# ============================================================
# Asosiy Ishga Tushirish
# ============================================================
if __name__ == "__main__":
    # Telegram Botni alohida oqimda (background thread) yoqish
    if BOT_TOKEN:
        bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        bot_thread.start()

    print(f"🚀 Veb server {PORT}-portda ishga tushmoqda...")
    app.run(host="0.0.0.0", port=PORT, debug=False)
