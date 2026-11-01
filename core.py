"""TTS core engine: website, API, and bot all use this module (Microsoft Edge Neural voices).

Handles voice resolution, text-to-speech synthesis, caching, and retry logic.
"""
import os
import re
import hmac
import time
import asyncio
import threading
from collections import OrderedDict

import edge_tts

from config import MAX_CHARS, CACHE_MB, MAX_JOBS, BOT_TOKEN

CACHE_BYTES = int(CACHE_MB * 1e6)
JOBS = threading.BoundedSemaphore(MAX_JOBS)
DEFAULT_VOICE = "uz-UZ-SardorNeural"

# Fallback voice list used when Microsoft's API is unreachable
FALLBACK = [
    ("uz-UZ-SardorNeural", "male"), ("uz-UZ-MadinaNeural", "female"),
    ("ru-RU-DmitryNeural", "male"), ("ru-RU-SvetlanaNeural", "female"),
    ("tr-TR-AhmetNeural", "male"), ("tr-TR-EmelNeural", "female"),
    ("en-US-AndrewNeural", "male"), ("en-US-AriaNeural", "female"),
    ("kk-KZ-DauletNeural", "male"), ("kk-KZ-AigulNeural", "female"),
]

# Language → (male voice, female voice) quick lookup
PAIRS = {
    "uz": ("uz-UZ-SardorNeural", "uz-UZ-MadinaNeural"),
    "ru": ("ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural"),
    "en": ("en-US-AndrewNeural", "en-US-AriaNeural"),
    "tr": ("tr-TR-AhmetNeural", "tr-TR-EmelNeural"),
    "kk": ("kk-KZ-DauletNeural", "kk-KZ-AigulNeural"),
}

GENDERS = {
    "male": {"male", "m", "man", "erkak", "муж", "мужской"},
    "female": {"female", "f", "woman", "ayol", "жен", "женский"},
}

# Voice styles: name, rate offset %, pitch offset Hz, volume offset %
STYLES = {
    "natural": ("Tabiiy", 0, 0, 0),
    "deep": ("Dev — chuqur va og'ir", -20, -40, 10),
    "chipmunk": ("Minion — ingichka va tez", 25, 55, 0),
    "hype": ("Reklama — tez va baland", 45, 8, 20),
    "calm": ("Sokin — sekin va yumshoq", -35, -8, -35),
}

FULL_ID = re.compile(r"[a-z]{2,3}-[A-Za-z0-9]+-[A-Za-z0-9-]+Neural")
SECRET = (BOT_TOKEN or os.urandom(16).hex()).encode()


def sign(text, voice):
    """Generate HMAC signature for trusted inline requests (bypass IP rate limit)."""
    return hmac.new(SECRET, f"{voice}\0{text}".encode(), "sha256").hexdigest()[:16]


class Busy(Exception):
    """Too many requests."""


def _voice_entry(v):
    name = v["ShortName"].split("-", 2)[-1].replace("Neural", "")
    return {
        "id": v["ShortName"],
        "name": name,
        "lang": v["Locale"],
        "gender": "male" if v["Gender"] == "Male" else "female",
    }


_vo = {"t": 0, "v": None}


def voices():
    """Return voice list (cached for 24 hours, fallback list on error)."""
    if _vo["v"] and time.time() - _vo["t"] < 86400:
        return _vo["v"]
    try:
        _vo["v"] = [_voice_entry(v) for v in asyncio.run(edge_tts.list_voices())]
        _vo["t"] = time.time()
    except Exception as exc:
        print(f"⚠️ Voice list unavailable: {exc}", flush=True)
        if not _vo["v"]:
            _vo["v"] = [
                _voice_entry({
                    "ShortName": i,
                    "Locale": i[:5],
                    "Gender": "Male" if g == "male" else "Female",
                })
                for i, g in FALLBACK
            ]
        _vo["t"] = time.time() - 86400 + 300  # retry in 5 minutes
    return _vo["v"]


def _gender(g):
    g = str(g or "").strip().lower()
    return next((k for k, words in GENDERS.items() if g in words), None)


def _pick(lang, gender):
    l = lang.lower().replace("_", "-")
    base, g = l.split("-")[0], _gender(gender)
    if l == base and base in PAIRS:
        return PAIRS[base][g == "female"]
    cand = [
        x for x in voices()
        if x["lang"].lower() == l or (l == base and x["lang"].lower().startswith(base + "-"))
    ]
    if g:
        cand = [x for x in cand if x["gender"] == g] or cand
    if not cand:
        raise ValueError(f"Language not found: {lang}. See: /api/voices")
    return sorted(cand, key=lambda x: (x["gender"] != "male", x["id"]))[0]["id"]


def resolve_voice(v=None, lang=None, gender=None):
    """Resolve voice ID from name, language code, or full ID.

    Accepts: full ID, name ('madina'), language ('ru'), language+gender ('uz-female'),
    or separate lang= and gender= parameters.
    """
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
                raise ValueError(f"Voice not found: {v}. See: /api/voices")
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
    """Build edge-tts parameters from request data (voice, style, rate, pitch, volume)."""
    style = str(d.get("style") or "natural").lower()
    if style not in STYLES:
        raise ValueError(f"Style not found: {style}. Available: {', '.join(STYLES)}")
    _, sr, sp, sv = STYLES[style]
    rate = round(_num(d.get("rate")) + sr)
    pitch = round(_num(d.get("pitch")) + sp)
    vol = round(_num(d.get("volume")) + sv)
    return {
        "voice": resolve_voice(d.get("voice") or d.get("v"), d.get("lang"), d.get("gender")),
        "rate": f"{max(-60, min(150, rate)):+d}%",
        "pitch": f"{max(-100, min(100, pitch)):+d}Hz",
        "volume": f"{max(-60, min(60, vol)):+d}%",
    }


# ─── In-memory LRU cache ───
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
    async for c in edge_tts.Communicate(
        text, o["voice"], rate=o["rate"], pitch=o["pitch"], volume=o["volume"]
    ).stream():
        if c["type"] == "audio":
            buf += c["data"]
    if not buf:
        raise ValueError("Empty audio returned")
    return bytes(buf)


# Microsoft multilingual voices — used as fallback when the primary voice returns silence
MULTI = {"male": "en-US-AndrewMultilingualNeural", "female": "en-US-AvaMultilingualNeural"}


class Audio(bytes):
    """MP3 bytes with .voice attribute indicating the actual voice used."""
    voice = None


def _silent(exc):
    """Check if Microsoft returned empty/silent audio."""
    s = str(exc)
    return "No audio" in s or "Empty audio" in s or "bo'sh audio" in s


def _store(key, data, voice):
    audio = Audio(data)
    audio.voice = voice
    _put(key, audio)
    return audio


def synth(text, o, on_miss=None, tries=3):
    """Synthesize text to MP3 (Audio bytes).

    Returns cached result if available; otherwise calls on_miss() for rate limiting,
    then attempts synthesis with retries and multilingual voice fallback.
    """
    key = (text, o["voice"], o["rate"], o["pitch"], o["volume"])
    hit = _get(key)
    if hit:
        return hit
    if on_miss:
        on_miss()
    plain = {**o, "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"}
    attempts = [o, o, plain, plain] if tries >= 3 else [o] * tries
    last = None
    with JOBS:
        for i, opt in enumerate(attempts):
            try:
                return _store(key, asyncio.run(_run(text, opt)), o["voice"])
            except Exception as exc:
                last = exc
                print(f"⚠️ TTS attempt {i + 1}/{len(attempts)} [{o['voice']}]: {type(exc).__name__}: {exc}", flush=True)
                if i < len(attempts) - 1:
                    time.sleep(0.6 * (i + 1))
        if _silent(last) and "Multilingual" not in o["voice"]:
            gender = next((x["gender"] for x in voices() if x["id"] == o["voice"]), "male")
            alt = {**o, "voice": MULTI[gender]}
            try:
                audio = _store(key, asyncio.run(_run(text, alt)), alt["voice"])
                print(f"↪️ {o['voice']} silent after {len(attempts)} attempts — used {alt['voice']}", flush=True)
                return audio
            except Exception as exc:
                last = exc
                print(f"⚠️ Fallback voice also failed [{alt['voice']}]: {type(exc).__name__}: {exc}", flush=True)
    raise RuntimeError(f"Voice generation failed: {last}")
