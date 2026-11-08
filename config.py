"""Uzbekcha TTS — Centralized configuration.

All environment variables and project-wide constants are defined here.
Change the canonical URL in one place to update all references.
"""
import os

# ─── Project identity ───
PROJECT_NAME = "Uzbekcha TTS"
PROJECT_DESCRIPTION = "Free Uzbek Text-to-Speech — Natural Uzbek AI Voice Generator"
PROJECT_VERSION = "2.0.0"

# ─── URLs (centralized — change here, applies everywhere) ───
PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL", "https://tts-uzbek.onrender.com"
).strip().rstrip("/")

GITHUB_URL = os.environ.get(
    "GITHUB_URL", "https://github.com/developer-uzbek/tts-uzbek"
).strip()

# ─── Telegram ───
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Uzbekcha_tts_bot").strip().lstrip("@")
BOT_URL = f"https://t.me/{BOT_USERNAME}"
ADMIN_IDS = os.environ.get("ADMIN_ID", "") + " " + os.environ.get("ADMIN_IDS", "")

# ─── Server ───
PORT = int(os.environ.get("PORT", 5000))
RATE_PER_MIN = int(os.environ.get("RATE_PER_MIN", 40))
DEFAULT_AUDIO_FILENAME = os.environ.get("DEFAULT_AUDIO_FILENAME", "uzbekcha_tts").strip() or "uzbekcha_tts"

# ─── TTS engine ───
MAX_CHARS = int(os.environ.get("MAX_CHARS", 5000))
CACHE_MB = float(os.environ.get("CACHE_MB", 24))
MAX_JOBS = int(os.environ.get("MAX_JOBS", 4))
