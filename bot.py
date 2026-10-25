"""
Free & Unlimited AI Text-to-Speech Telegram Bot
Ishga tushirish uchun hech qanday pullik API kerak emas.
"""

import os
import io
import asyncio
import telebot
from telebot import types
import edge_tts

# BOT TOKEN: BotFather'dan olingan token (yoki muhit o'zgaruvchisidan)
BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Foydalanuvchilar sozlamalari (xotirada saqlanadi)
USER_SETTINGS = {}

VOICE_MAP = {
    "uz_sardor": ("uz-UZ-SardorNeural", "🇺🇿 Sardor (Erkak)"),
    "uz_madina": ("uz-UZ-MadinaNeural", "🇺🇿 Madina (Ayol)"),
    "tr_ahmet": ("tr-TR-AhmetNeural", "🇹🇷 Ahmet (Turkcha)"),
    "ru_dmitry": ("ru-RU-DmitryNeural", "🇷🇺 Dmitry (Ruscha)"),
    "en_guy": ("en-US-GuyNeural", "🇺🇸 Guy (Inglizcha)"),
}

async def generate_audio_stream(text: str, voice: str = "uz-UZ-SardorNeural", rate: str = "+0%") -> io.BytesIO:
    """Matnni xotiradagi (RAM) MP3 buferiga aylantiradi."""
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf

def get_voice_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("🇺🇿 Sardor (Erkak)", callback_data="v_uz_sardor"),
        types.InlineKeyboardButton("🇺🇿 Madina (Ayol)", callback_data="v_uz_madina"),
        types.InlineKeyboardButton("🇹🇷 Ahmet", callback_data="v_tr_ahmet"),
        types.InlineKeyboardButton("🇷🇺 Dmitry", callback_data="v_ru_dmitry"),
        types.InlineKeyboardButton("🇺🇸 Guy (US)", callback_data="v_en_guy"),
    ]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    uid = message.from_user.id
    if uid not in USER_SETTINGS:
        USER_SETTINGS[uid] = {"voice": "uz-UZ-SardorNeural", "name": "🇺🇿 Sardor (Erkak)", "rate": "+10%"}

    text = (
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Men matnlarni <b>professional sun'iy intellekt ovoziga</b> aylantirib beruvchi bepul botman.\n\n"
        f"🎙️ <b>Hozirgi ovoz:</b> {USER_SETTINGS[uid]['name']}\n\n"
        "✍️ <i>Menga istalgan matn yuboring, men darhol ovozli xabar qilib tashlab beraman!</i>\n"
        "Ovozni o'zgartirish uchun /voice buyrug'ini bosing."
    )
    bot.reply_to(message, text, reply_markup=get_voice_keyboard())

@bot.message_handler(commands=['voice'])
def change_voice(message):
    bot.reply_to(message, "🎙️ <b>O'zingizga ma'qul ovozni tanlang:</b>", reply_markup=get_voice_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("v_"))
def callback_voice(call):
    uid = call.from_user.id
    key = call.data.replace("v_", "")
    if key in VOICE_MAP:
        voice_id, voice_name = VOICE_MAP[key]
        if uid not in USER_SETTINGS:
            USER_SETTINGS[uid] = {"rate": "+10%"}
        USER_SETTINGS[uid]["voice"] = voice_id
        USER_SETTINGS[uid]["name"] = voice_name
        
        bot.answer_callback_query(call.id, f"Tanlandi: {voice_name}")
        bot.edit_message_text(
            f"✅ <b>Ovoz o'zgartirildi!</b>\n\nHozirgi tanlangan ovoz: <b>{voice_name}</b>\n\nEndi matningizni yozib yuboring:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text.strip()
    if not text:
        return

    uid = message.from_user.id
    settings = USER_SETTINGS.get(uid, {"voice": "uz-UZ-SardorNeural", "name": "🇺🇿 Sardor (Erkak)", "rate": "+10%"})

    # "Yozmoqda..." yoki "Ovoz yozmoqda..." holatini ko'rsatish
    bot.send_chat_action(message.chat.id, "record_audio")

    try:
        # Audio yaratish
        audio_buf = asyncio.run(generate_audio_stream(
            text=text,
            voice=settings["voice"],
            rate=settings["rate"]
        ))

        # Telegram ovozli xabari (Voice message) sifatida yuborish
        audio_buf.name = "voice.ogg"
        bot.send_voice(
            chat_id=message.chat.id,
            voice=audio_buf,
            caption=f"🎙️ Ovoz: <b>{settings['name']}</b>",
            reply_to_message_id=message.message_id
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik yuz berdi: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 Telegram Bot ishga tushdi...")
    print("=" * 50)
    bot.infinity_polling(skip_pending=True)
