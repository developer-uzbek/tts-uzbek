"""TTS yadrosi: sayt, API va bot shu yerdan foydalanadi (Microsoft Edge Neural ovozlari)."""
import os
import re
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
    ("uz-UZ-SardorNeural", "Erkak"), ("uz-UZ-MadinaNeural", "Ayol"),
    ("ru-RU-DmitryNeural", "Erkak"), ("ru-RU-SvetlanaNeural", "Ayol"),
    ("tr-TR-AhmetNeural", "Erkak"), ("tr-TR-EmelNeural", "Ayol"),
    ("en-US-AndrewNeural", "Erkak"), ("en-US-AriaNeural", "Ayol"),
    ("kk-KZ-DauletNeural", "Erkak"), ("kk-KZ-AigulNeural", "Ayol"),
]
LANG_DEFAULT = {"uz": "uz-UZ-SardorNeural", "ru": "ru-RU-DmitryNeural", "tr": "tr-TR-AhmetNeural",
                "en": "en-US-AndrewNeural", "kk": "kk-KZ-DauletNeural"}

# stil = tezlik(%), ton(Hz), ovoz balandligi(%) qo'shimchasi. Slayderlar ustiga qo'shiladi.
STYLES = {
    "natural": ("Standard / Natural", 0, 0, 0), "narrator": ("Narrator", -3, -2, 0),
    "robot": ("Robot", 8, 6, 3), "minion": ("Minion", 18, 10, 6),
    "dramatic": ("Dramatic", 5, 12, 10), "whisper": ("Whisper", -10, -5, -5),
    "cinematic": ("Cinematic", 2, 8, 8),
}


class Busy(Exception):
    """Juda ko'p so'rov."""


def _voice_entry(v):
    name = v["ShortName"].split("-", 2)[-1].replace("Neural", "")
    return {"id": v["ShortName"], "name": name, "lang": v["Locale"],
            "gender": "Erkak" if v["Gender"] == "Male" else "Ayol"}


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
            _vo["v"] = [_voice_entry({"ShortName": i, "Locale": i[:5], "Gender": "Male" if g == "Erkak" else "Female"})
                        for i, g in FALLBACK]
        _vo["t"] = time.time() - 86400 + 300  # 5 daqiqadan keyin qayta uriniladi
    return _vo["v"]


def resolve_voice(v):
    """'sardor', 'uz', 'uz-UZ-MadinaNeural' -> to'liq ovoz ID."""
    v = str(v or "").strip()
    if not v:
        return DEFAULT_VOICE
    if re.fullmatch(r"[a-z]{2,3}-[A-Za-z0-9]+-[A-Za-z0-9-]+Neural", v):
        return v
    low = v.lower()
    if low in LANG_DEFAULT:
        return LANG_DEFAULT[low]
    for x in voices():
        if x["name"].lower() == low or x["id"].lower() == low:
            return x["id"]
    raise ValueError(f"Ovoz topilmadi: {v}. Ro'yxat: /api/voices")


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
    return {"voice": resolve_voice(d.get("voice") or d.get("v")),
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


def synth(text, o, on_miss=None, tries=3):
    """Matn -> MP3 bytes. Kesh bo'lsa darrov qaytadi; yo'q bo'lsa on_miss() (limit tekshiruvi) chaqiriladi."""
    key = (text, o["voice"], o["rate"], o["pitch"], o["volume"])
    hit = _get(key)
    if hit:
        return hit
    if on_miss:
        on_miss()
    last = None
    with JOBS:
        for i in range(tries):
            try:
                data = asyncio.run(_run(text, o))
                _put(key, data)
                return data
            except Exception as exc:
                last = exc
                print(f"⚠️ TTS urinish {i + 1}/{tries}: {exc}", flush=True)
                time.sleep(0.8 * (i + 1))
    raise RuntimeError(f"Ovoz yaratilmadi: {last}")
