"""Telegram bot: matn -> ovoz + admin paneli (post yuborish, majburiy obuna, pauza, statistika).

Holat (foydalanuvchilar, kanallar, pauza) kichik state.json faylda saqlanadi — alohida baza yo'q.
Render free tarifda fayl qayta deploy'da o'chadi, shuning uchun o'zgarishlar adminga Telegram orqali
zaxira nusxa (pin qilingan JSON) sifatida yuboriladi va bot qayta ishga tushganda shundan tiklanadi.
"""
import io
import os
import hashlib
import re
import json
import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode, quote
from pathlib import Path

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

import core

TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMINS = [int(x) for x in re.findall(r"\d+", os.environ.get("ADMIN_ID", "") + " " + os.environ.get("ADMIN_IDS", ""))]
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Uzbekcha_tts_bot").strip().lstrip("@")
APP_URL = os.environ.get("PUBLIC_BASE_URL", "https://tts-uzbek.onrender.com").strip().rstrip("/")
STATE_FILE = Path(os.environ.get("STATE_FILE") or Path(__file__).with_name("state.json"))
BACKUP_NAME = "tts_backup.json"
BACKUP_EVERY = float(os.environ.get("BACKUP_HOURS", 6)) * 3600
TZ = float(os.environ.get("TZ_HOURS", 5)) * 3600  # Toshkent = UTC+5
BOT_MAX_CHARS = 4000
START = time.time()
ACTIVE = False

VOICES = {
    "sardor": ("uz-UZ-SardorNeural", "🇺🇿 Sardor"), "madina": ("uz-UZ-MadinaNeural", "🇺🇿 Madina"),
    "ahmet": ("tr-TR-AhmetNeural", "🇹🇷 Ahmet"), "emel": ("tr-TR-EmelNeural", "🇹🇷 Emel"),
    "dmitry": ("ru-RU-DmitryNeural", "🇷🇺 Dmitry"), "svetlana": ("ru-RU-SvetlanaNeural", "🇷🇺 Svetlana"),
    "andrew": ("en-US-AndrewNeural", "🇺🇸 Andrew"), "aria": ("en-US-AriaNeural", "🇺🇸 Aria"),
}

bot = telebot.TeleBot(TOKEN or "0:none", parse_mode="HTML", num_threads=8)
LOCK = threading.Lock()
FLAGS = {"save": False, "backup": False, "last_bk": 0.0, "bk_msg": 0}
WAIT, POST, OK_UNTIL, HITS = {}, {}, {}, {}   # admin kutayotgan kiritish / tasdiqlanayotgan post / obuna keshi / bot limiti
ME = {}


def norm_channel(v):
    v = re.sub(r"^(https?://)?(t\.me/|telegram\.me/)", "", str(v or "").strip()).strip("/@ ")
    return f"@{v}" if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,31}", v) else None


S = {
    "users": {},                      # {user_id: [qo'shilgan_kun, oxirgi_faol_kun, ovoz]}
    "sub_on": os.environ.get("SUBSCRIBE_REQUIRED", "true").strip().lower() in {"1", "true", "yes", "on"},
    "channels": [c for c in (norm_channel(x) for x in os.environ.get("TELEGRAM_CHANNEL", "").split(",")) if c and c != "@tgchannel"],
    "pause_until": 0,
    "inline": 0,                      # inline orqali tayyorlangan natijalar soni
}


# ---------- holat ----------
def day():
    return int((time.time() + TZ) // 86400)


def load():
    try:
        S.update(json.loads(STATE_FILE.read_text("utf-8")))
    except FileNotFoundError:
        pass
    except Exception as exc:
        print(f"⚠️ state.json o'qilmadi: {exc}", flush=True)
    return bool(S["users"])


def save():
    with LOCK:
        raw = json.dumps(S, separators=(",", ":"))
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(raw, "utf-8")
    tmp.replace(STATE_FILE)


def touch(uid, voice=None):
    k, d = str(uid), day()
    with LOCK:
        u = S["users"].get(k)
        if u is None:
            u = S["users"][k] = [d, d, "sardor"]
            FLAGS["backup"] = True
        u[1] = d
        if voice:
            u[2] = voice
        FLAGS["save"] = True
    return u


def touch_known(uid):
    if str(uid) in S["users"]:
        touch(uid)


def backup():
    with LOCK:
        raw = json.dumps(S, ensure_ascii=False).encode()
    f = io.BytesIO(raw)
    f.name = BACKUP_NAME
    msg = bot.send_document(ADMINS[0], f, disable_notification=True,
                            caption="💾 Avtomatik zaxira nusxa. Bot qayta ishga tushganda shu fayldan tiklanadi.")
    old, FLAGS["bk_msg"], FLAGS["last_bk"] = FLAGS["bk_msg"], msg.message_id, time.time()
    try:
        bot.pin_chat_message(ADMINS[0], msg.message_id, disable_notification=True)
        if old:
            bot.delete_message(ADMINS[0], old)
    except Exception:
        pass


def restore():
    for a in ADMINS:
        try:
            pm = bot.get_chat(a).pinned_message
            if pm and pm.document and pm.document.file_name == BACKUP_NAME:
                data = json.loads(bot.download_file(bot.get_file(pm.document.file_id).file_path))
                if isinstance(data.get("users"), dict):
                    S.update(data)
                    FLAGS["bk_msg"] = pm.message_id
                    return True
        except Exception as exc:
            print(f"⚠️ Zaxiradan tiklab bo'lmadi: {exc}", flush=True)
    return False


def maintenance():
    while True:
        time.sleep(60)
        try:
            if FLAGS["save"]:
                FLAGS["save"] = False
                save()
            if FLAGS["backup"] and ADMINS and time.time() - FLAGS["last_bk"] > BACKUP_EVERY:
                FLAGS["backup"] = False
                backup()
        except Exception as exc:
            print(f"⚠️ Texnik xizmat xatosi: {exc}", flush=True)


# ---------- yordamchilar ----------
def parse_dur(text):
    """'30' / '45m' / '2 soat' / '3d' / '1 kun' -> soniya (0 = noto'g'ri)."""
    m = re.fullmatch(r"\s*(\d+)\s*([A-Za-z']*)\s*", text or "")
    if not m:
        return 0
    n, u = int(m.group(1)), m.group(2).lower()
    if not u or u.startswith(("daq", "min", "m")):
        k = 60
    elif u.startswith(("soat", "h", "s")):
        k = 3600
    elif u.startswith(("kun", "k", "d")):
        k = 86400
    else:
        return 0
    return min(n * k, 365 * 86400)


def fmt_left(sec):
    d, r = divmod(int(sec), 86400)
    h, r = divmod(r, 3600)
    m = r // 60
    parts = ([f"{d} kun"] if d else []) + ([f"{h} soat"] if h else [])
    if m or not parts:
        parts.append(f"{max(m, 1)} daqiqa")
    return " ".join(parts)


def btn(text, data):
    return types.InlineKeyboardButton(text, callback_data=data)


def unsubscribed(uid):
    """Obuna bo'lmagan kanallar ro'yxati (musbat natija 5 daqiqa keshlanadi)."""
    if not (S["sub_on"] and S["channels"]) or OK_UNTIL.get(uid, 0) > time.time():
        return []
    miss = []
    for ch in S["channels"]:
        try:
            if bot.get_chat_member(ch, uid).status not in ("member", "administrator", "creator", "restricted"):
                miss.append(ch)
        except ApiTelegramException as exc:  # kanal noto'g'ri sozlangan — foydalanuvchini to'smaymiz
            print(f"⚠️ Obuna tekshiruvi ({ch}): {exc}", flush=True)
    if not miss:
        OK_UNTIL[uid] = time.time() + 300
    return miss


def allowed(uid, chat_id):
    """Foydalanuvchini hisobga oladi va pauza / majburiy obunani tekshiradi. Adminlar hamisha o'tadi."""
    touch(uid)
    if uid in ADMINS:
        return True
    left = S["pause_until"] - time.time()
    if left > 0:
        bot.send_message(chat_id, f"⏸ Bot vaqtincha to'xtatilgan. Taxminan <b>{fmt_left(left)}</b> dan so'ng qaytadi.")
        return False
    miss = unsubscribed(uid)
    if miss:
        kb = types.InlineKeyboardMarkup(row_width=1)
        for ch in miss:
            kb.add(types.InlineKeyboardButton(f"📣 {ch}", url=f"https://t.me/{ch[1:]}"))
        kb.add(btn("✅ Tekshirish", "chk"))
        bot.send_message(chat_id, "📣 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling, so'ng <b>Tekshirish</b> tugmasini bosing.", reply_markup=kb)
        return False
    return True


def throttle(uid, limit=10, kind="msg"):
    q = HITS.setdefault((uid, kind), deque())
    now = time.time()
    while q and q[0] < now - 60:
        q.popleft()
    if len(q) >= limit:
        raise core.Busy(f"Daqiqada {limit} tadan ortiq so'rov yuborib bo'lmaydi. Biroz kuting.")
    q.append(now)


def voice_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(*[btn(name, f"v:{k}") for k, (_, name) in VOICES.items()])
    return kb


def welcome(uid):
    name = VOICES.get(S["users"].get(str(uid), [0, 0, ""])[2], VOICES["sardor"])[1]
    extra = "\n🛠 Admin paneli: /admin" if uid in ADMINS else ""
    return ("👋 <b>Assalomu alaykum!</b>\n\nMatnni tabiiy ovozga aylantirib beraman — bepul va cheksiz.\n\n"
            f"🎙 Hozirgi ovoz: <b>{name}</b>\n✍️ Menga istalgan matn yuboring.\n"
            f"💬 Istalgan chatda: <code>@{BOT_USERNAME} matn</code>\n"
            f"🌐 Sayt: {APP_URL}\n🔗 Havola orqali: <code>{APP_URL}/?q=Salom</code>{extra}")


# ---------- foydalanuvchi buyruqlari ----------
@bot.message_handler(commands=["id"])
def cmd_id(m):
    bot.reply_to(m, f"🆔 Sizning Telegram ID: <code>{m.from_user.id}</code>\n\nBuni Render'da <b>ADMIN_ID</b> ga yozing.")


@bot.message_handler(commands=["start", "help"])
def cmd_start(m):
    if allowed(m.from_user.id, m.chat.id):
        bot.send_message(m.chat.id, welcome(m.from_user.id), reply_markup=voice_kb(), disable_web_page_preview=True)


@bot.message_handler(commands=["voice"])
def cmd_voice(m):
    if allowed(m.from_user.id, m.chat.id):
        bot.send_message(m.chat.id, "🎙 Ovozni tanlang:", reply_markup=voice_kb())


@bot.callback_query_handler(func=lambda c: c.data == "chk")
def cb_check(c):
    OK_UNTIL.pop(c.from_user.id, None)
    if unsubscribed(c.from_user.id):
        bot.answer_callback_query(c.id, "Hali obuna bo'lmagansiz ❌", show_alert=True)
    else:
        bot.answer_callback_query(c.id, "Rahmat! ✅")
        bot.send_message(c.message.chat.id, welcome(c.from_user.id), reply_markup=voice_kb(), disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda c: c.data.startswith("v:"))
def cb_voice(c):
    key = c.data[2:]
    if not allowed(c.from_user.id, c.message.chat.id) or key not in VOICES:
        return bot.answer_callback_query(c.id)
    touch(c.from_user.id, key)
    bot.answer_callback_query(c.id, f"Tanlandi: {VOICES[key][1]}")
    bot.edit_message_text(f"✅ Ovoz: <b>{VOICES[key][1]}</b>\n\nEndi matn yuboring.", c.message.chat.id, c.message.message_id)


# ---------- admin paneli ----------
def stats_text():
    d, U = day(), list(S["users"].values())
    paused = S["pause_until"] - time.time()
    return (f"📊 <b>Statistika</b>\n\n👥 Jami foydalanuvchi: <b>{len(U)}</b>\n🆕 Bugun qo'shilgan: <b>{sum(u[0] == d for u in U)}</b>\n"
            f"🟢 Bugun faol: <b>{sum(u[1] == d for u in U)}</b>\n📅 7 kunda faol: <b>{sum(u[1] > d - 7 for u in U)}</b>\n\n"
            f"🔒 Majburiy obuna: <b>{'yoqiq' if S['sub_on'] and S['channels'] else 'oʻchiq'}</b> ({len(S['channels'])} ta kanal)\n"
            f"⏸ Bot: <b>{'to‘xtatilgan, ' + fmt_left(paused) + ' qoldi' if paused > 0 else 'ishlayapti'}</b>\n"
            f"🔎 Inline natijalar: <b>{S.get('inline', 0)}</b>\n⏱ Ish vaqti: {fmt_left(time.time() - START)}")


def home_view():
    paused = S["pause_until"] > time.time()
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(btn("📢 Post yuborish", "a:post"), btn("📊 Statistika", "a:stat"),
           btn(f"🔒 Majburiy obuna: {'ON' if S['sub_on'] else 'OFF'}", "a:sub"),
           btn("▶️ Davom ettirish" if paused else "⏸ To'xtatish", "a:resume" if paused else "a:pause"))
    return f"🛠 <b>Admin paneli</b>\n\n👥 Foydalanuvchilar: <b>{len(S['users'])}</b>", kb


def sub_view():
    ch = S["channels"]
    lines = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(ch)) or "Kanal qo'shilmagan."
    note = "" if ch else "\n<i>Kanal qo'shilmaguncha obuna tekshirilmaydi.</i>"
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🔴 O'chirish" if S["sub_on"] else "🟢 Yoqish", "a:subtog"), btn("➕ Kanal qo'shish", "a:addch"))
    kb.add(*[btn(f"❌ {c} ni olib tashlash", f"a:rm:{i}") for i, c in enumerate(ch)])
    kb.add(btn("⬅️ Orqaga", "a:home"))
    return f"🔒 <b>Majburiy obuna: {'🟢 YOQIQ' if S['sub_on'] else '🔴 OʻCHIQ'}</b>\n\n{lines}{note}\n\n<i>Bot kanalda admin bo'lishi shart.</i>", kb


def pause_view():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(btn("10 daqiqa", "a:p:600"), btn("1 soat", "a:p:3600"), btn("6 soat", "a:p:21600"),
           btn("1 kun", "a:p:86400"), btn("7 kun", "a:p:604800"), btn("✍️ Boshqa vaqt", "a:pc"), btn("⬅️ Orqaga", "a:home"))
    return "⏸ <b>Botni qancha vaqtga to'xtatamiz?</b>\n\nAdminlar to'xtatilgan botdan foydalanishda davom etadi.", kb


def show(c, view):
    text, kb = view if isinstance(view, tuple) else (view, None)
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=kb)
    except ApiTelegramException:  # "message is not modified"
        pass


def set_pause(sec):
    S["pause_until"] = time.time() + sec if sec else 0
    FLAGS["save"] = FLAGS["backup"] = True


def broadcast(admin_chat, src_chat, src_msg):
    ids = [int(u) for u in S["users"]]
    ok = bad = 0
    status = bot.send_message(admin_chat, f"📤 Yuborilmoqda… 0/{len(ids)}")
    for i, uid in enumerate(ids, 1):
        for _ in range(2):
            try:
                bot.copy_message(uid, src_chat, src_msg)
                ok += 1
            except ApiTelegramException as exc:
                if exc.error_code == 429:
                    time.sleep((exc.result_json.get("parameters") or {}).get("retry_after", 5) + 1)
                    continue
                bad += 1
                if exc.error_code in (400, 403):  # bot bloklangan / chat yo'q — ro'yxatdan chiqaramiz
                    with LOCK:
                        S["users"].pop(str(uid), None)
            break
        else:
            bad += 1
        time.sleep(0.05)
        if i % 100 == 0:
            try:
                bot.edit_message_text(f"📤 Yuborilmoqda… {i}/{len(ids)}", admin_chat, status.message_id)
            except Exception:
                pass
    FLAGS["save"] = FLAGS["backup"] = True
    bot.edit_message_text(f"✅ Tugadi.\n\n📬 Yetkazildi: <b>{ok}</b>\n🚫 Yetkazilmadi (bloklagan): <b>{bad}</b>", admin_chat, status.message_id)


@bot.message_handler(commands=["admin"], func=lambda m: m.from_user.id in ADMINS)
def cmd_admin(m):
    WAIT.pop(m.from_user.id, None)
    text, kb = home_view()
    bot.send_message(m.chat.id, text, reply_markup=kb)


@bot.message_handler(commands=["pause"], func=lambda m: m.from_user.id in ADMINS)
def cmd_pause(m):  # /pause 2h  yoki  /pause 0
    arg = m.text.partition(" ")[2]
    sec = parse_dur(arg)
    if not sec and arg.strip() != "0":
        return bot.reply_to(m, "Masalan: <code>/pause 30m</code>, <code>/pause 2 soat</code>, <code>/pause 1 kun</code>, <code>/pause 0</code> (davom ettirish)")
    set_pause(sec)
    bot.reply_to(m, f"⏸ Bot <b>{fmt_left(sec)}</b>ga to'xtatildi." if sec else "▶️ Bot davom ettirildi.")


@bot.callback_query_handler(func=lambda c: c.data.startswith("a:") and c.from_user.id in ADMINS)
def cb_admin(c):
    uid, p = c.from_user.id, c.data.split(":")
    act = p[1]
    if act in {"home", "stat", "sub", "pause", "x"}:
        WAIT.pop(uid, None)
    if act in {"home", "x"}:
        POST.pop(uid, None)
        show(c, home_view())
    elif act == "stat":
        show(c, (stats_text(), types.InlineKeyboardMarkup().add(btn("⬅️ Orqaga", "a:home"))))
    elif act == "sub":
        show(c, sub_view())
    elif act == "subtog":
        S["sub_on"] = not S["sub_on"]
        FLAGS["save"] = FLAGS["backup"] = True
        show(c, sub_view())
    elif act == "rm" and int(p[2]) < len(S["channels"]):
        S["channels"].pop(int(p[2]))
        OK_UNTIL.clear()
        FLAGS["save"] = FLAGS["backup"] = True
        show(c, sub_view())
    elif act == "addch":
        WAIT[uid] = "channel"
        show(c, ("➕ Kanal <b>@username</b> yoki havolasini yuboring.\n\nBot avval shu kanalga <b>admin</b> qilib qo'shilgan bo'lishi kerak.",
                 types.InlineKeyboardMarkup().add(btn("🚫 Bekor qilish", "a:sub"))))
    elif act == "pause":
        show(c, pause_view())
    elif act == "p":
        set_pause(int(p[2]))
        show(c, (f"⏸ Bot <b>{fmt_left(int(p[2]))}</b>ga to'xtatildi.", types.InlineKeyboardMarkup().add(btn("⬅️ Panel", "a:home"))))
    elif act == "pc":
        WAIT[uid] = "pause"
        show(c, ("✍️ Vaqtni yozing. Masalan: <code>45 daqiqa</code>, <code>3 soat</code>, <code>2 kun</code> yoki <code>30m</code>, <code>5h</code>, <code>1d</code>",
                 types.InlineKeyboardMarkup().add(btn("🚫 Bekor qilish", "a:pause"))))
    elif act == "resume":
        set_pause(0)
        show(c, home_view())
    elif act == "post":
        WAIT[uid] = "post"
        show(c, ("📢 Yuboriladigan postni yozing: <b>matn</b> yoki <b>rasm</b> (izoh bilan). Formatlash va tugmalar saqlanadi.",
                 types.InlineKeyboardMarkup().add(btn("🚫 Bekor qilish", "a:x"))))
    elif act == "go" and uid in POST:
        src = POST.pop(uid)
        show(c, "📤 Yuborish boshlandi…")
        threading.Thread(target=broadcast, args=(c.message.chat.id, *src), daemon=True).start()
    bot.answer_callback_query(c.id)


ALL_TYPES = ["text", "photo", "video", "animation", "document", "audio", "voice", "sticker", "video_note"]


@bot.message_handler(func=lambda m: m.from_user.id in WAIT, content_types=ALL_TYPES)
def admin_input(m):
    uid, mode = m.from_user.id, WAIT[m.from_user.id]
    if mode == "post":
        WAIT.pop(uid)
        POST[uid] = (m.chat.id, m.message_id)
        kb = types.InlineKeyboardMarkup().add(btn(f"✅ Yuborish ({len(S['users'])} ta)", "a:go"), btn("❌ Bekor", "a:x"))
        bot.send_message(m.chat.id, "👆 Shu post barcha foydalanuvchilarga yuboriladi. Tasdiqlaysizmi?", reply_to_message_id=m.message_id, reply_markup=kb)
    elif mode == "channel":
        ch = norm_channel(m.text)
        if not ch:
            return bot.reply_to(m, "❌ Kanal <code>@username</code> ko'rinishida bo'lsin. Qayta yuboring yoki /admin.")
        try:
            ME.setdefault("id", bot.get_me().id)
            if bot.get_chat_member(ch, ME["id"]).status not in ("administrator", "creator"):
                raise ValueError("bot admin emas")
        except Exception:
            return bot.reply_to(m, f"❌ {ch} topilmadi yoki bot unda admin emas. Botni kanalga <b>admin</b> qilib qo'shing va qayta yuboring.")
        WAIT.pop(uid)
        if ch not in S["channels"]:
            S["channels"].append(ch)
        OK_UNTIL.clear()
        FLAGS["save"] = FLAGS["backup"] = True
        text, kb = sub_view()
        bot.send_message(m.chat.id, f"✅ {ch} qo'shildi.\n\n{text}", reply_markup=kb)
    elif mode == "pause":
        sec = parse_dur(m.text)
        if not sec:
            return bot.reply_to(m, "❌ Tushunmadim. Masalan: <code>45 daqiqa</code>, <code>3 soat</code>, <code>2 kun</code>.")
        WAIT.pop(uid)
        set_pause(sec)
        bot.send_message(m.chat.id, f"⏸ Bot <b>{fmt_left(sec)}</b>ga to'xtatildi.", reply_markup=types.InlineKeyboardMarkup().add(btn("⬅️ Panel", "a:home")))


@bot.message_handler(content_types=["document"], func=lambda m: m.from_user.id in ADMINS and (m.document.file_name or "").endswith(".json"))
def admin_restore(m):  # zaxira faylni qo'lda tiklash
    try:
        data = json.loads(bot.download_file(bot.get_file(m.document.file_id).file_path))
        assert isinstance(data["users"], dict)
        with LOCK:
            S.update(data)
        FLAGS["save"] = True
        bot.reply_to(m, f"✅ Tiklandi: <b>{len(S['users'])}</b> foydalanuvchi.")
    except Exception:
        bot.reply_to(m, "❌ Bu zaxira fayl emas.")


# ---------- matn -> ovoz ----------
@bot.message_handler(content_types=["text"])
def on_text(m):
    uid = m.from_user.id
    if not allowed(uid, m.chat.id) or m.text.startswith("/"):
        return
    text = m.text.strip()
    if len(text) > BOT_MAX_CHARS:
        return bot.reply_to(m, f"⚠️ Matn juda uzun ({len(text)}). {BOT_MAX_CHARS} belgidan kamroq yuboring yoki saytdan foydalaning: {APP_URL}")
    vid, vname = VOICES.get(S["users"][str(uid)][2], VOICES["sardor"])
    bot.send_chat_action(m.chat.id, "record_voice")
    try:
        data = core.synth(text, core.opts({"voice": vid, "rate": "+10"}), on_miss=lambda: throttle(uid))
        f = io.BytesIO(data)
        f.name = "voice.mp3"
        bot.send_voice(m.chat.id, f, caption=f"🎙 {vname}", reply_to_message_id=m.message_id)
    except core.Busy as exc:
        bot.reply_to(m, f"⏳ {exc}")
    except Exception as exc:
        print(f"❌ Bot TTS xatosi: {exc}", flush=True)
        bot.reply_to(m, "❌ Ovoz yaratib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.")


# ---------- inline rejim: istalgan chatda  @bot matn ----------
INLINE_MAX = 200          # belgi (Telegram o'zi 256 bilan cheklaydi; audio havola uzun bo'lmasligi uchun)
INLINE_DELAY = 0.7        # foydalanuvchi yozishni to'xtatguncha kutamiz — har harfga TTS qilmaymiz
LATEST, POOL = {}, ThreadPoolExecutor(4)   # foydalanuvchi -> oxirgi so'rov ID / parallel sintez


def short(text, n=48):
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def article(key, title, desc, msg=None):
    return types.InlineQueryResultArticle(key, title, types.InputTextMessageContent(msg or f"🎙 @{BOT_USERNAME}"), description=desc)


def inline_audio(text, key, uid):
    """Matnni sintez qiladi (kesh isiydi, xato oldindan bilinadi) va audio natija qaytaradi.
    Telegram MP3 ni bizning /tts.mp3 havolamizdan oladi — u keshdan darrov beriladi."""
    vid, vname = VOICES.get(key, VOICES["sardor"])
    core.synth(text, core.opts({"voice": vid, "rate": "+10"}), on_miss=lambda: throttle(uid, 30, "inline"), tries=1)
    url = f"{APP_URL}/tts.mp3?" + urlencode({"q": text, "voice": vid, "rate": 10, "sig": core.sign(text, vid)}, quote_via=quote)
    return types.InlineQueryResultAudio(hashlib.md5(f"{vid}{text}".encode()).hexdigest(), url, f"🔊 {short(text)}",
                                        caption=f"@{BOT_USERNAME}", performer=f"{vname} • TTS")


def inline_work(q, text, reply):
    uid = q.from_user.id
    if LATEST.get(uid) != q.id:       # foydalanuvchi yozishda davom etdi — bu so'rov eskirgan
        return
    saved = S["users"].get(str(uid), [0, 0, "sardor"])[2]
    keys = ([saved] + [k for k in ("sardor", "madina") if k != saved])[:2]   # o'zining ovozi + 1 ta muqobil
    futures = [POOL.submit(inline_audio, text, k, uid) for k in keys]
    results, busy = [], False
    for f in futures:
        try:
            results.append(f.result())
        except core.Busy:
            busy = True
        except Exception as exc:
            print(f"❌ Inline TTS xatosi: {exc}", flush=True)
    if LATEST.get(uid) != q.id:
        return
    if results:
        S["inline"] = S.get("inline", 0) + 1
        FLAGS["save"] = True
        return reply(results, cache=300)   # bir xil matn 5 daqiqa Telegram tomonida ham keshlanadi
    if busy:
        return reply([article("busy", "⏳ Biroz kuting", "Juda tez-tez so'rov yuboryapsiz. Bir daqiqadan so'ng qayta yozing.")])
    reply([article("fail", "❌ Audio yaratib bo'lmadi", "Birozdan so'ng qayta urinib ko'ring yoki matnni o'zgartiring.")])


@bot.inline_handler(func=lambda q: True)
def on_inline(q):
    uid, text = q.from_user.id, (q.query or "").strip()
    LATEST[uid] = q.id

    def reply(results, cache=0, button=None):
        try:
            bot.answer_inline_query(q.id, results, cache_time=cache, is_personal=True, button=button)
        except Exception as exc:       # so'rov eskirgan bo'lishi mumkin
            print(f"⚠️ answerInlineQuery: {exc}", flush=True)

    to_bot = types.InlineQueryResultsButton("🎙 Botni ochish", start_parameter="inline")
    if not text:
        return reply([article("hint", "✍️ Matn yozing", f"Masalan: @{BOT_USERNAME} Salom, dunyo!", f"🎙 @{BOT_USERNAME} matn")], button=to_bot)
    if len(text) > INLINE_MAX:
        return reply([article("long", "⚠️ Matn juda uzun", f"Ko'pi bilan {INLINE_MAX} belgi (hozir {len(text)}). Uzun matn uchun botga yoki saytga o'ting.", APP_URL)], button=to_bot)
    touch_known(uid)
    if uid not in ADMINS:
        left = S["pause_until"] - time.time()
        if left > 0:
            return reply([article("pause", "⏸ Bot vaqtincha to'xtatilgan", f"Taxminan {fmt_left(left)} dan so'ng qaytadi.")])
        if unsubscribed(uid):
            return reply([article("sub", "📣 Avval kanalga obuna bo'ling", "Botni oching va ko'rsatilgan kanallarga obuna bo'ling.")], button=to_bot)
    threading.Timer(INLINE_DELAY, inline_work, (q, text, reply)).start()


def run():
    global ACTIVE
    if not ADMINS:
        print("ℹ️ ADMIN_ID o'rnatilmagan — admin paneli o'chiq. ID ni bilish uchun botga /id yozing.", flush=True)
    if not load() and ADMINS and restore():
        FLAGS["last_bk"] = time.time()
        print(f"♻️ Zaxiradan tiklandi: {len(S['users'])} foydalanuvchi.", flush=True)
    threading.Thread(target=maintenance, daemon=True).start()
    try:
        bot.remove_webhook()
    except Exception:
        pass
    while True:
        try:
            ACTIVE = True
            print(f"✅ Telegram bot ishga tushdi | adminlar: {ADMINS or '—'}", flush=True)
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as exc:
            ACTIVE = False
            print(f"⚠️ Bot xatosi: {exc}. 5 soniyadan so'ng qayta ulanadi…", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    run()
