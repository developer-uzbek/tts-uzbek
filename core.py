"""TTS yadrosi: sayt, API va bot shu yerdan foydalanadi (Microsoft Edge Neural ovozlari)."""
import os
import re
import hmac
import time
import asyncio
import threading
from collections import OrderedDict

import edge_tts

MAX_CHARS = int(os.environ.get("MAX_CHARS", 5000))          # bitta so'rov uchun (sayt matnni o'zi bo'laklaydi)
CACHE_BYTES = int(float(os.environ.get("CACHE_MB", 24)) * 1e6)
JOBS = threading.BoundedSemaphore(int(os.environ.get("MAX_JOBS", 4)))  # bir vaqtda nechta sintez (free tarif uchun)
DEFAULT_VOICE = "uz-UZ-SardorNeural"

# Ovoz ro'yxati Microsoft'dan olinmasa shu ishlatiladi
FALLBACK = [
    ("uz-UZ-SardorNeural", "male"), ("uz-UZ-MadinaNeural", "female"),
    ("ru-RU-DmitryNeural", "male"), ("ru-RU-SvetlanaNeural", "female"),
    ("tr-TR-AhmetNeural", "male"), ("tr-TR-EmelNeural", "female"),
    ("en-US-AndrewNeural", "male"), ("en-US-AriaNeural", "female"),
    ("kk-KZ-DauletNeural", "male"), ("kk-KZ-AigulNeural", "female"),
]
# til -> (erkak, ayol): `lang=ru&gender=female` yoki `voice=ru-female` shu yerdan tanlaydi
PAIRS = {"uz": ("uz-UZ-SardorNeural", "uz-UZ-MadinaNeural"), "ru": ("ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural"),
         "en": ("en-US-AndrewNeural", "en-US-AriaNeural"), "tr": ("tr-TR-AhmetNeural", "tr-TR-EmelNeural"),
         "kk": ("kk-KZ-DauletNeural", "kk-KZ-AigulNeural")}
GENDERS = {"male": {"male", "m", "man", "erkak", "муж", "мужской"},
           "female": {"female", "f", "woman", "ayol", "жен", "женский"}}

# stil = tezlik(%), ton(Hz), ovoz balandligi(%) qo'shimchasi. Slayderlar ustiga qo'shiladi.
# Edge TTS faqat shu uch o'lchovni beradi, shuning uchun stillar ataylab ekstremal tanlangan.
STYLES = {
    "natural": ("Tabiiy", 0, 0, 0),
    "deep": ("Dev — chuqur va og'ir", -20, -40, 10),
    "chipmunk": ("Minion — ingichka va tez", 25, 55, 0),
    "hype": ("Reklama — tez va baland", 45, 8, 20),
    "calm": ("Sokin — sekin va yumshoq", -35, -8, -35),
}
FULL_ID = re.compile(r"[a-z]{2,3}-[A-Za-z0-9]+-[A-Za-z0-9-]+Neural")
SECRET = (os.environ.get("BOT_TOKEN") or os.urandom(16).hex()).encode()


def sign(text, voice):
    """Bot yuboradigan inline havolalar uchun imzo: shu imzoli so'rovlar IP limitiga tushmaydi."""
    return hmac.new(SECRET, f"{voice}\0{text}".encode(), "sha256").hexdigest()[:16]


class Busy(Exception):
    """Juda ko'p so'rov."""


def _voice_entry(v):
    name = v["ShortName"].split("-", 2)[-1].replace("Neural", "")
    return {"id": v["ShortName"], "name": name, "lang": v["Locale"],
            "gender": "male" if v["Gender"] == "Male" else "female"}


_vo = {"t": 0, "v": None}


def voices():
    """Ovozlar ro'yxati (24 soat keshlanadi, xato bo'lsa zaxira ro'yxat)."""
    if _vo["v"] and time.time() - _vo["t"] < 86400:
        return _vo["v"]
    try:
        _vo["v"] = [_voice_entry(v) for v in asyncio.run(edge_tts.list_voices())]
        _vo["t"] = time.time()
    except Exception as exc:
        print(f"⚠️ Ovozlar ro'yxati olinmadi: {exc}", flush=True)
        if not _vo["v"]:
            _vo["v"] = [_voice_entry({"ShortName": i, "Locale": i[:5], "Gender": "Male" if g == "male" else "Female"})
                        for i, g in FALLBACK]
        _vo["t"] = time.time() - 86400 + 300  # 5 daqiqadan keyin qayta uriniladi
    return _vo["v"]


def _gender(g):
    g = str(g or "").strip().lower()
    return next((k for k, words in GENDERS.items() if g in words), None)


def _pick(lang, gender):
    l = lang.lower().replace("_", "-")
    base, g = l.split("-")[0], _gender(gender)
    if l == base and base in PAIRS:
        return PAIRS[base][g == "female"]
    cand = [x for x in voices() if x["lang"].lower() == l or (l == base and x["lang"].lower().startswith(base + "-"))]
    if g:
        cand = [x for x in cand if x["gender"] == g] or cand
    if not cand:
        raise ValueError(f"Til topilmadi: {lang}. Ro'yxat: /api/voices")
    return sorted(cand, key=lambda x: (x["gender"] != "male", x["id"]))[0]["id"]


def resolve_voice(v=None, lang=None, gender=None):
    """Ovoz ID. Qabul qiladi: to'liq ID, ism ('madina'), til ('ru'), til+jins ('uz-female', 'ru_male')
    yoki alohida lang= va gender= (male/female, erkak/ayol)."""
    v, lang = str(v or "").strip(), str(lang or "").strip()
    if FULL_ID.fullmatch(v):
        return v
    low = v.lower()
    if low:
        for x in voices():
            if low in (x["name"].lower(), x["id"].lower()):
                return x["id"]
        if not lang:
            p = re.split(r"[-_ ]+", low)
            rest = [x for x in p[1:] if not _gender(x)]
            if not re.fullmatch(r"[a-z]{2,3}", p[0]) or len(rest) > 1:
                raise ValueError(f"Ovoz topilmadi: {v}. Ro'yxat: /api/voices")
            lang = "-".join([p[0]] + rest)
            gender = gender or next((x for x in p[1:] if _gender(x)), None)
    if not lang:
        if not gender:
            return DEFAULT_VOICE
        lang = "uz"
    return _pick(lang, gender)


def _num(v, default=0, lo=-100, hi=100):
    m = re.search(r"-?\d+(?:\.\d+)?", str(v if v is not None else ""))
    return max(lo, min(hi, float(m.group()))) if m else default


def opts(d):
    """So'rov parametrlaridan (voice, style, rate, pitch, volume) edge-tts qiymatlarini yasaydi."""
    style = str(d.get("style") or "natural").lower()
    if style not in STYLES:
        raise ValueError(f"Stil topilmadi: {style}. Mavjud: {', '.join(STYLES)}")
    _, sr, sp, sv = STYLES[style]
    rate = round(_num(d.get("rate")) + sr)
    pitch = round(_num(d.get("pitch")) + sp)
    vol = round(_num(d.get("volume")) + sv)
    return {"voice": resolve_voice(d.get("voice") or d.get("v"), d.get("lang"), d.get("gender")),
            "rate": f"{max(-60, min(150, rate)):+d}%",
            "pitch": f"{max(-100, min(100, pitch)):+d}Hz",
            "volume": f"{max(-60, min(60, vol)):+d}%"}


_cache, _size, _lock = OrderedDict(), [0], threading.Lock()


def _get(key):
    with _lock:
        v = _cache.get(key)
        if v:
            _cache.move_to_end(key)
        return v


def _put(key, data):
    if len(data) > CACHE_BYTES // 4:
        return
    with _lock:
        if key in _cache:
            return
        _cache[key] = data
        _size[0] += len(data)
        while _size[0] > CACHE_BYTES:
            _size[0] -= len(_cache.popitem(last=False)[1])


async def _run(text, o):
    buf = bytearray()
    async for c in edge_tts.Communicate(text, o["voice"], rate=o["rate"], pitch=o["pitch"], volume=o["volume"]).stream():
        if c["type"] == "audio":
            buf += c["data"]
    if not buf:
        raise ValueError("bo'sh audio qaytdi")
    return bytes(buf)


# Microsoft'ning ko'p tilli ovozlari matn tilini o'zi aniqlaydi (turkcha, o'zbekcha, ruscha...).
# Oddiy ovoz (masalan Ahmet) jim chiqsa, shu ovozlar zaxira bo'lib ishlaydi.
MULTI = {"male": "en-US-AndrewMultilingualNeural", "female": "en-US-AvaMultilingualNeural"}
SAMPLE = {"tr": "Merhaba", "uz": "Salom", "ru": "Привет", "kk": "Сәлем", "en": "Hello"}   # ovoz sog'ligini tekshirish uchun
DEAD_TTL = 3600
_dead = {}   # Microsoft hozir jim qaytarayotgan ovozlar: ovoz -> belgilangan vaqt (1 soatdan so'ng qayta tekshiriladi)


def _silent(exc):
    """Microsoft jim (bo'sh) audio qaytardi — ovoz bu matnni o'qiy olmadi."""
    s = str(exc)
    return "No audio" in s or "bo'sh audio" in s


def dead_voices():
    now = time.time()
    return [v for v, t in _dead.items() if now - t < DEAD_TTL]


def _probe(o):
    """Ovoz o'z tilidagi bitta so'zni ham o'qiy olmasa — ovozning o'zi buzilgan: 1 soatga zaxiraga o'tkaziladi."""
    sample = SAMPLE.get(o["voice"][:2])
    if not sample:
        return
    try:
        asyncio.run(_run(sample, o))
        _dead.pop(o["voice"], None)
    except Exception as exc:
        if _silent(exc):
            _dead[o["voice"]] = time.time()
            print(f"🚫 {o['voice']} Microsoft tomonida jim — {DEAD_TTL // 60} daqiqaga zaxira ovozga o'tkazildi", flush=True)


def synth(text, o, on_miss=None, tries=3):
    """Matn -> MP3 bytes. Kesh bo'lsa darrov qaytadi; yo'q bo'lsa on_miss() (limit tekshiruvi) chaqiriladi.
    Ovoz jim chiqsa (yoki yaqinda jim chiqqan bo'lsa), o'sha jinsdagi ko'p tilli ovozga o'tadi."""
    key = (text, o["voice"], o["rate"], o["pitch"], o["volume"])
    hit = _get(key)
    if hit:
        return hit
    if on_miss:
        on_miss()
    last = None
    with JOBS:
        primary = o["voice"] not in dead_voices()
        for i in range(tries if primary else 0):
            try:
                data = asyncio.run(_run(text, o))
                _put(key, data)
                return data
            except Exception as exc:
                last = exc
                print(f"⚠️ TTS urinish {i + 1}/{tries} [{o['voice']}]: {type(exc).__name__}: {exc}", flush=True)
                if _silent(exc) and i >= 1:          # takror urinish foyda bermaydi — zaxira ovozga o'tamiz
                    break
                if i < tries - 1:
                    time.sleep(0.8 * (i + 1))
        if (not primary or _silent(last)) and "Multilingual" not in o["voice"]:
            gender = next((x["gender"] for x in voices() if x["id"] == o["voice"]), "male")
            alt = {**o, "voice": MULTI[gender]}
            try:
                data = asyncio.run(_run(text, alt))
                _put(key, data)                      # asl kalit bilan keshlanadi: qayta so'rov darrov qaytadi
                if primary:                          # ovoz buzilganmi yoki matn tilga mos kelmadimi — fonda tekshiramiz
                    threading.Thread(target=_probe, args=(o,), daemon=True).start()
                print(f"↪️ {o['voice']} o'rniga {alt['voice']} ishlatildi", flush=True)
                return data
            except Exception as exc:
                last = exc
                print(f"⚠️ Zaxira ovoz ham ishlamadi [{alt['voice']}]: {type(exc).__name__}: {exc}", flush=True)
    raise RuntimeError(f"Ovoz yaratilmadi: {last}")
