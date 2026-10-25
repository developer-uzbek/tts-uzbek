"""
Free & Unlimited AI Text-to-Speech Telegram Bot
"""

import os
import io
import asyncio
import telebot
from telebot import types
import edge_tts

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
SUBSCRIBE_REQUIRED = os.getenv("SUBSCRIBE_REQUIRED", "true").strip().lower() in {"1", "true", "yes", "on"}
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "@tgchannel").strip()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
USER_SETTINGS = {}

VOICE_MAP = {
    "uz_sardor": ("uz-UZ-SardorNeural", "🇺🇿 Sardor (Erkak)"),
    "uz_madina": ("uz-UZ-MadinaNeural", "🇺🇿 Madina (Ayol)"),
    "tr_ahmet": ("tr-TR-AhmetNeural", "🇹🇷 Ahmet (Turkcha)"),
    "ru_dmitry": ("ru-RU-DmitryNeural", "🇷🇺 Dmitry (Ruscha)"),
    "en_alex": ("en-US-AlexNeural", "🇺🇸 Alex (Inglizcha)"),
}


def get_channel_username(value):
    if not value:
        return ""
    val = str(value).strip()
    if val.startswith("@"):
        return val
    if val.startswith("https://t.me/"):
        return "@" + val.split("/", 3)[-1].strip("/")
    if val.startswith("t.me/"):
        return "@" + val.replace("t.me/", "").strip("/")
    return "@" + val


def check_subscribed(user_id):
    if not SUBSCRIBE_REQUIRED or not TELEGRAM_CHANNEL:
        return True
    channel = get_channel_username(TELEGRAM_CHANNEL)
    try:
        member = bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in {"member", "administrator", "creator"}
    except Exception:
        return False


async def generate_audio_stream(text: str, voice: str = "uz-UZ-SardorNeural", rate: str = "+0%") -> io.BytesIO:
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
        types.InlineKeyboardButton("🇺🇸 Alex", callback_data="v_en_alex"),
    ]
    markup.add(*buttons)
    return markup


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    uid = message.from_user.id
    if uid not in USER_SETTINGS:
        USER_SETTINGS[uid] = {"voice": "uz-UZ-SardorNeural", "name": "🇺🇿 Sardor (Erkak)", "rate": "+10%"}

    if not check_subscribed(uid):
        channel = get_channel_username(TELEGRAM_CHANNEL)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📣 Kanalga o'tish", url=f"https://t.me/{channel.lstrip('@')}"))
        bot.reply_to(message, f"📣 Ushbu botdan foydalanish uchun avval <b>{channel}</b> kanaliga obuna bo'ling.", reply_markup=markup)
        return

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
    if not check_subscribed(message.from_user.id):
        channel = get_channel_username(TELEGRAM_CHANNEL)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📣 Kanalga o'tish", url=f"https://t.me/{channel.lstrip('@')}"))
        bot.reply_to(message, f"📣 Botdan foydalanish uchun avval <b>{channel}</b> kanaliga obuna bo'ling.", reply_markup=markup)
        return
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
            message_id=call.message.message_id,
        )


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if not check_subscribed(message.from_user.id):
        channel = get_channel_username(TELEGRAM_CHANNEL)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📣 Kanalga o'tish", url=f"https://t.me/{channel.lstrip('@')}"))
        bot.reply_to(message, f"📣 Botdan foydalanish uchun avval <b>{channel}</b> kanaliga obuna bo'ling.", reply_markup=markup)
        return

    text = message.text.strip()
    if not text:
        return

    uid = message.from_user.id
    settings = USER_SETTINGS.get(uid, {"voice": "uz-UZ-SardorNeural", "name": "🇺🇿 Sardor (Erkak)", "rate": "+10%"})
    bot.send_chat_action(message.chat.id, "record_audio")

    try:
        audio_buf = asyncio.run(generate_audio_stream(text=text, voice=settings["voice"], rate=settings["rate"]))
        audio_buf.name = "voice.ogg"
        bot.send_voice(chat_id=message.chat.id, voice=audio_buf, caption=f"🎙️ Ovoz: <b>{settings['name']}</b>", reply_to_message_id=message.message_id)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik yuz berdi: {str(e)}")


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 Telegram Bot ishga tushdi...")
    print("=" * 50)
    bot.infinity_polling(skip_pending=True)
