"""Uzbekcha TTS — Ovoz klonlash moduli (o'z ovozingizda gapirtirish).

G'oya (ikki bosqichli konveyer):
  1. Talaffuz va o'zbekcha ohang — Microsoft Edge Neural (Sardor / Madina) beradi.
  2. Siz yozgan ovozdan "ovoz DNK'si" (profil) olinadi va sintez qilingan nutq
     shu profilga moslashtiriladi:
        - PROSODIYA : ohang balandligi, intonatsiya, tempo, pauzalar (Praat/Parselmouth)
        - TEMBR     : neyron (OpenVoice V2 Tone Color Converter) YOKI yengil DSP
                      (formant siljitish + spektr/EQ moslash)
        - SIFAT     : xirillash/havo (HNR), energiya, umumiy balandlik

Ikki dvigatel:
  "neural" — OpenVoice o'rnatilgan bo'lsa (eng yaxshi natija, ~80-90% o'xshashlik)
  "lite"   — hech qanday og'ir model kerak emas, darhol ishlaydi (~50-65% o'xshashlik)
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
import zlib
from pathlib import Path

import numpy as np

try:  # tahlil kutubxonalari (requirements-clone.txt)
    import librosa
    import parselmouth
    import soundfile as sf
    from parselmouth.praat import call
    from scipy.signal import find_peaks, butter, sosfilt
    DEPS_ERROR = None
except Exception as _exc:  # pragma: no cover
    DEPS_ERROR = f"{type(_exc).__name__}: {_exc}"

SR = 22050
BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIR = Path(os.environ.get("CLONE_DIR", BASE_DIR / "voice_profiles"))
CKPT_DIR = Path(os.environ.get("OPENVOICE_CKPT", BASE_DIR / "checkpoints_v2"))
MAX_REF_SECONDS = 90
MAX_CLONE_CHARS = int(os.environ.get("MAX_CLONE_CHARS", 1500))
MAX_SENTENCES = 20
ID_RE = re.compile(r"^[a-f0-9]{12}$")

BAND_EDGES = np.geomspace(80, 8000, 25)            # 24 ta chastota polosasi
BAND_CENTERS = np.sqrt(BAND_EDGES[:-1] * BAND_EDGES[1:])

# O'zbekcha o'qish matni (turli tovushlar: o', g', sh, ch, ng, savol, undov, raqam)
READING_TEXT = (
    "Assalomu alaykum! Mening ismim — ovoz egasi. Bugun men o'zimning ovozimni "
    "kompyuterga o'rgatyapman. O'zbekiston — Markaziy Osiyoning qoq markazida joylashgan, "
    "qadimiy va go'zal davlat. Samarqand, Buxoro va Xiva shaharlarining tarixi ming yillarga "
    "borib taqaladi. Siz hech tog'ga chiqqanmisiz? Men bahor faslida chegaradosh tog'lar "
    "etagida sayr qilishni yaxshi ko'raman. Ertalab soat yettida turib, choy ichaman, "
    "so'ng ishga shoshilaman. Voy, qanday ajoyib kun! Yigirma besh yil avval bu yerda "
    "hech narsa yo'q edi. Hozir esa shahar tinmay rivojlanmoqda. Maktab, bog'cha va "
    "kutubxonalar qurilmoqda, yoshlar esa ilm-fan sari intilmoqda. Xullas, hayot davom etadi, "
    "va biz uning har bir lahzasidan zavqlanishimiz kerak."
)


# ───────────────────────────── yordamchi: audio I/O ─────────────────────────────

def _need_deps():
    if DEPS_ERROR:
        raise RuntimeError(
            "Klonlash kutubxonalari o'rnatilmagan: pip install -r requirements-clone.txt "
            f"({DEPS_ERROR})"
        )


def decode_audio(data: bytes, suffix: str = ".webm") -> np.ndarray:
    """Istalgan audio (webm/ogg/mp3/wav/m4a) -> mono float32, 22.05 kHz."""
    _need_deps()
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / f"in{suffix if re.fullmatch(r'\.[A-Za-z0-9]{1,5}', suffix) else '.bin'}"
        dst = Path(td) / "out.wav"
        src.write_bytes(data)
        if shutil.which("ffmpeg"):
            r = subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ac", "1", "-ar", str(SR), "-f", "wav", str(dst)],
                capture_output=True,
            )
            if r.returncode != 0 or not dst.exists():
                raise ValueError("Audioni o'qib bo'lmadi: " + r.stderr.decode(errors="ignore")[:200])
            y, _ = sf.read(str(dst), dtype="float32")
        else:  # ffmpeg yo'q — faqat wav/flac/ogg ishlaydi
            try:
                y, sr = sf.read(str(src), dtype="float32")
            except Exception:
                raise RuntimeError("ffmpeg topilmadi. ffmpeg o'rnating (README'ga qarang).")
            if y.ndim > 1:
                y = y.mean(1)
            if sr != SR:
                y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    return np.asarray(y, dtype=np.float32)


def encode_audio(y: np.ndarray, fmt: str = "mp3") -> tuple[bytes, str]:
    y = np.clip(y, -1, 1).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, y, SR, format="WAV", subtype="PCM_16")
    wav = buf.getvalue()
    if fmt == "wav" or not shutil.which("ffmpeg"):
        return wav, "audio/wav"
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "wav", "-i", "pipe:0", "-codec:a", "libmp3lame", "-q:a", "2", "-f", "mp3", "pipe:1"],
        input=wav, capture_output=True,
    )
    if r.returncode != 0 or not r.stdout:
        return wav, "audio/wav"
    return r.stdout, "audio/mpeg"


# ───────────────────────────── tahlil (ovoz DNK'si) ─────────────────────────────

def _runs(mask: np.ndarray):
    """True qiymatlarning (boshi, oxiri) intervallari."""
    if not mask.any():
        return []
    d = np.diff(np.concatenate([[0], mask.astype(np.int8), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def _active_mask(y: np.ndarray, hop=220):
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=hop)[0]
    db = 20 * np.log10(np.maximum(rms, 1e-7))
    p95, floor = np.percentile(db, 95), np.percentile(db, 10)
    thr = min(max(p95 - 35, floor + 10, -70), p95 - 12)
    m = db > thr
    # 120 ms dan qisqa bo'shliqlarni to'ldirish, 60 ms dan qisqa bo'laklarni o'chirish
    for s, e in _runs(~m):
        if s > 0 and e < len(m) and (e - s) < 12:
            m[s:e] = True
    for s, e in _runs(m):
        if (e - s) < 6:
            m[s:e] = False
    return m, db


def _ltas(y: np.ndarray) -> np.ndarray:
    """Uzoq muddatli o'rtacha spektr: 24 ta polosa (dB)."""
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256)) ** 2
    e = 10 * np.log10(S.sum(0) + 1e-12)
    act = e > (np.percentile(e, 95) - 30)
    if act.sum() < 3:
        act[:] = True
    P = S[:, act].mean(1)
    f = librosa.fft_frequencies(sr=SR, n_fft=1024)
    out = []
    for lo, hi in zip(BAND_EDGES[:-1], BAND_EDGES[1:]):
        sel = (f >= lo) & (f < hi)
        out.append(10 * np.log10(P[sel].mean() + 1e-12) if sel.any() else -120.0)
    return np.array(out)


def _f(x, nd=2):
    try:
        x = float(x)
        return None if (np.isnan(x) or np.isinf(x)) else round(x, nd)
    except Exception:
        return None


def analyze(y: np.ndarray) -> dict:
    """Nutqdan 10 ta ovoz xususiyati + uslub teglari."""
    _need_deps()
    y = np.asarray(y, dtype=np.float32)
    y = y - np.mean(y)
    total = len(y) / SR
    if total < 3:
        raise ValueError("Yozuv juda qisqa (kamida 3 soniya, tavsiya: 30+ soniya).")

    snd = parselmouth.Sound(y.astype(np.float64), SR)

    # 1) PITCH (ohang balandligi) va 2) INTONATSIYA diapazoni
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=70, pitch_ceiling=450)
    f0 = pitch.selected_array["frequency"]
    voiced = f0 > 0
    if voiced.sum() < 30:
        raise ValueError("Ovoz yetarli aniqlanmadi. Shovqinsiz joyda, mikrofonga yaqinroq gapiring.")
    f0v = f0[voiced]
    st = 12 * np.log2(f0v / 100.0)
    p5, p50, p95 = np.percentile(f0v, [5, 50, 95])
    # kontur dinamikasi (urg'u/ritm): ketma-ket ovozli kadrlar orasidagi o'zgarish tezligi
    both = voiced[1:] & voiced[:-1]
    st_all = np.where(voiced, 12 * np.log2(np.maximum(f0, 1) / 100.0), 0)
    slope = np.abs(np.diff(st_all))[both] / 0.01
    slope = slope[slope < 80]

    # 3) TEMPO + 4) PAUZALAR
    act, rms_db = _active_mask(y)
    hop_s = 220 / SR
    runs = _runs(act)
    if not runs:
        raise ValueError("Nutq topilmadi.")
    first, last = runs[0][0], runs[-1][1]
    span = (last - first) * hop_s
    pauses = [(s2 - e1) * hop_s for (_, e1), (s2, _) in zip(runs[:-1], runs[1:])]
    pauses = [p for p in pauses if p >= 0.2]
    pause_total = float(sum(pauses))
    art_time = max(span - pause_total, 0.5)

    inten = snd.to_intensity(minimum_pitch=70, time_step=0.01)
    iv = inten.values[0]
    pk, _ = find_peaks(iv, prominence=2.0, height=np.percentile(iv, 90) - 25)
    n_syl = 0
    for i in pk:
        t = inten.xs()[i]
        v = pitch.get_value_at_time(t)
        if v and not np.isnan(v):
            n_syl += 1

    # 5) ENERGIYA
    act_db = rms_db[act]
    rms_mean = float(np.mean(act_db))
    dyn_range = float(np.percentile(act_db, 95) - np.percentile(act_db, 10))

    # 6) YORQINLIK (spektral)
    bands = _ltas(y)
    tilt = float(np.polyfit(np.log2(BAND_CENTERS), bands, 1)[0])  # dB/oktava
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256))
    cen = librosa.feature.spectral_centroid(S=S, sr=SR)[0]
    e = S.sum(0)
    centroid = float(np.mean(cen[e > np.percentile(e, 60)]))

    # 7) OVOZ SIFATI: jitter / shimmer / HNR
    jitter = shimmer = hnr = None
    try:
        pp = call(snd, "To PointProcess (periodic, cc)", 70, 450)
        jitter = call(pp, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        shimmer = call([snd, pp], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        hnr = call(snd.to_harmonicity_cc(time_step=0.01, minimum_pitch=75), "Get mean", 0, 0)
    except Exception:
        pass

    # 8) FORMANTLAR (F1-F3: tomoq/og'iz bo'shlig'i — ovoz tembrining asosi)
    maxf = 5500 if p50 > 165 else 5000
    fm = snd.to_formant_burg(time_step=0.01, max_number_of_formants=5, maximum_formant=maxf)
    ts = pitch.xs()[voiced][::3]
    F = {1: [], 2: [], 3: []}
    for t in ts:
        for k in F:
            v = fm.get_value_at_time(k, t)
            if v and not np.isnan(v):
                F[k].append(v)
    formants = [float(np.median(F[k])) if len(F[k]) > 10 else None for k in (1, 2, 3)]

    clip = float(np.mean(np.abs(y) > 0.99))
    snr = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 8))

    p = {
        "f0_median": _f(p50, 1), "f0_mean": _f(np.mean(f0v), 1),
        "f0_p5": _f(p5, 1), "f0_p95": _f(p95, 1),
        "f0_range_st": _f(12 * np.log2(p95 / p5)), "f0_std_st": _f(np.std(st)),
        "contour_speed": _f(np.median(slope) if len(slope) else 0),
        "speech_rate": _f(n_syl / max(span, 0.5)), "art_rate": _f(n_syl / art_time),
        "pause_ratio": _f(pause_total / max(span, 0.5), 3),
        "pause_mean": _f(np.mean(pauses) if pauses else 0.4, 3),
        "pause_median": _f(np.median(pauses) if pauses else 0.4, 3),
        "pauses_per_min": _f(len(pauses) / max(span, 1) * 60, 1),
        "rms_db": _f(rms_mean, 1), "dyn_range_db": _f(dyn_range, 1),
        "tilt_db_oct": _f(tilt), "centroid_hz": _f(centroid, 0),
        "jitter": _f(jitter, 4), "shimmer": _f(shimmer, 4), "hnr_db": _f(hnr, 1),
        "f1": _f(formants[0], 0), "f2": _f(formants[1], 0), "f3": _f(formants[2], 0),
        "ltas": [round(float(b), 2) for b in bands],
        "duration": _f(total, 1), "voiced_seconds": _f(voiced.sum() * 0.01, 1),
        "syllables": int(n_syl),
        "gender_guess": "male" if p50 < 165 else "female",
        "snr_db": _f(snr, 1), "clip_ratio": _f(clip, 5),
    }
    p["style"] = describe(p)
    p["quality"] = quality_notes(p)
    return p


def describe(p: dict) -> dict:
    """Raqamlardan stil (uslub) teglari."""
    ar = p.get("art_rate") or 5
    tempo = "tez" if ar > 6.0 else "sekin" if ar < 4.2 else "o'rtacha"
    sd = p.get("f0_std_st") or 3
    expr = "ekspressiv" if sd > 4.2 else "monoton / vazmin" if sd < 2.2 else "tabiiy"
    tilt = p.get("tilt_db_oct") or -8
    bright = "yorqin / ravshan" if tilt > -6 else "iliq / yumshoq" if tilt < -10 else "muvozanatli"
    pr = p.get("pause_ratio") or 0.15
    rhythm = "ko'p to'xtaydi (o'ylanib)" if pr > 0.28 else "ravon, uzluksiz" if pr < 0.1 else "o'rtacha pauzali"
    hnr = p.get("hnr_db")
    texture = "sof, tiniq" if hnr and hnr > 17 else "havodor / xirillagan" if hnr and hnr < 11 else "oddiy"
    pitch = p.get("f0_median") or 130
    reg = "past (bas)" if pitch < 110 else "o'rta" if pitch < 190 else "baland"
    return {"tempo": tempo, "ifodalilik": expr, "yorqinlik": bright, "ritm": rhythm,
            "tekstura": texture, "registr": reg}


def quality_notes(p: dict) -> list[str]:
    w = []
    if (p["voiced_seconds"] or 0) < 10:
        w.append("Ovozli qism juda kam. Kamida 30 soniya (yaxshisi 60 soniya) yozing.")
    elif (p["voiced_seconds"] or 0) < 25:
        w.append("Yozuv qisqa: 45–60 soniya bo'lsa, o'xshashlik ancha yaxshilanadi.")
    if (p["snr_db"] or 99) < 22:
        w.append("Fon shovqini sezilarli. Tinch xonada, mikrofonga 10–15 sm yaqin gapiring.")
    if (p["clip_ratio"] or 0) > 0.001:
        w.append("Ovoz qirqilgan (clipping). Mikrofon kuchaytirishini pasaytiring.")
    if (p["rms_db"] or -20) < -42:
        w.append("Yozuv juda past. Mikrofonga yaqinroq gapiring.")
    return w


# ───────────────────────────── profillar ─────────────────────────────

def _pdir(pid: str) -> Path:
    if not ID_RE.fullmatch(pid or ""):
        raise ValueError("Noto'g'ri profil ID.")
    return PROFILE_DIR / pid


def create_profile(chunks: list[np.ndarray], name: str) -> dict:
    """Bir nechta yozuvdan profil yaratish va saqlash."""
    _need_deps()
    y = np.concatenate([np.pad(c, (0, int(0.4 * SR))) for c in chunks])
    y = y[: MAX_REF_SECONDS * SR]
    peak = np.max(np.abs(y)) or 1.0
    y = (y / peak * 0.9).astype(np.float32)
    prof = analyze(y)
    pid = uuid.uuid4().hex[:12]
    d = _pdir(pid)
    d.mkdir(parents=True, exist_ok=True)
    sf.write(str(d / "ref.wav"), y, SR, subtype="PCM_16")
    prof.update({"id": pid, "name": (name or "Mening ovozim").strip()[:40], "created": int(time.time())})
    (d / "profile.json").write_text(json.dumps(prof, ensure_ascii=False, indent=1), encoding="utf-8")
    return prof


def load_profile(pid: str) -> dict:
    f = _pdir(pid) / "profile.json"
    if not f.exists():
        raise ValueError("Profil topilmadi.")
    return json.loads(f.read_text(encoding="utf-8"))


def list_profiles() -> list[dict]:
    out = []
    if PROFILE_DIR.exists():
        for d in sorted(PROFILE_DIR.iterdir()):
            f = d / "profile.json"
            if ID_RE.fullmatch(d.name) and f.exists():
                try:
                    p = json.loads(f.read_text(encoding="utf-8"))
                    out.append({k: p.get(k) for k in ("id", "name", "created", "duration", "f0_median", "gender_guess")})
                except Exception:
                    pass
    return sorted(out, key=lambda x: -(x.get("created") or 0))


def delete_profile(pid: str) -> bool:
    d = _pdir(pid)
    if d.exists():
        shutil.rmtree(d)
        return True
    return False


# ───────────────────────────── neyron dvigatel (OpenVoice V2) ─────────────────────────────

class _Neural:
    _conv = None
    _lock = threading.Lock()
    _src_cache: dict = {}

    @staticmethod
    def status() -> tuple[bool, str]:
        if DEPS_ERROR:
            return False, "Asosiy kutubxonalar yo'q"
        if not (importlib.util.find_spec("torch") and importlib.util.find_spec("openvoice")):
            return False, "OpenVoice/torch o'rnatilmagan"
        if not (CKPT_DIR / "converter" / "checkpoint.pth").exists():
            return False, f"Model fayllari yo'q ({CKPT_DIR}/converter/)"
        return True, "tayyor"

    @classmethod
    def get(cls):
        with cls._lock:
            if cls._conv is None:
                import torch
                from openvoice.api import OpenVoiceBaseClass, ToneColorConverter

                class _TCC(ToneColorConverter):  # wavmark/watermark'siz
                    def __init__(self, cfg, device):
                        OpenVoiceBaseClass.__init__(self, cfg, device)
                        self.watermark_model = None
                        self.version = getattr(self.hps, "_version_", "v1")

                dev = "cuda:0" if torch.cuda.is_available() else "cpu"
                c = _TCC(str(CKPT_DIR / "converter" / "config.json"), dev)
                c.load_ckpt(str(CKPT_DIR / "converter" / "checkpoint.pth"))
                cls._conv = c
            return cls._conv

    @classmethod
    def convert(cls, y: np.ndarray, pid: str, tau: float = 0.3) -> np.ndarray:
        import torch
        c = cls.get()
        d = _pdir(pid)
        se_path = d / "se.pth"
        with cls._lock, tempfile.TemporaryDirectory() as td:
            if se_path.exists():
                tgt = torch.load(str(se_path), map_location=c.device)
            else:
                tgt = c.extract_se(str(d / "ref.wav"), se_save_path=str(se_path)).to(c.device)
            src_wav = Path(td) / "src.wav"
            sf.write(str(src_wav), y, SR, subtype="PCM_16")
            src = c.extract_se(str(src_wav))
            out = c.convert(str(src_wav), src, tgt, tau=tau)
        out = np.asarray(out, dtype=np.float32)
        sr_out = c.hps.data.sampling_rate
        return librosa.resample(out, orig_sr=sr_out, target_sr=SR) if sr_out != SR else out


def engines() -> dict:
    ok, why = _Neural.status()
    return {
        "lite": {"available": DEPS_ERROR is None, "note": DEPS_ERROR or "tayyor"},
        "neural": {"available": ok, "note": why},
        "ffmpeg": bool(shutil.which("ffmpeg")),
    }


# ───────────────────────────── DSP bosqichlari ─────────────────────────────

def _praat_adjust(y, pitch_ratio=1.0, range_factor=1.0, dur_factor=1.0, formant_ratio=1.0):
    """Praat 'Change gender': pitch median, pitch range, davomiylik va formantlarni o'zgartiradi."""
    if (abs(pitch_ratio - 1) < 0.01 and abs(range_factor - 1) < 0.03
            and abs(dur_factor - 1) < 0.02 and abs(formant_ratio - 1) < 0.01):
        return y
    snd = parselmouth.Sound(y.astype(np.float64), SR)
    pt = snd.to_pitch(time_step=0.01, pitch_floor=70, pitch_ceiling=500)
    fv = pt.selected_array["frequency"]
    fv = fv[fv > 0]
    med = float(np.median(fv)) if len(fv) > 5 else 0.0
    new_med = med * pitch_ratio if med else 0
    try:
        out = call(snd, "Change gender", 70, 500, float(formant_ratio), float(new_med),
                   float(range_factor), float(dur_factor))
        arr = np.asarray(out.values[0], dtype=np.float32)
        return arr if len(arr) > 100 else y
    except Exception:
        return y


def _eq_match(y, target_bands, strength):
    """Spektral yorqinlik/tembr egri chizig'ini foydalanuvchiniki bilan moslash."""
    if strength <= 0.01:
        return y
    cur = _ltas(y)
    t = np.asarray(target_bands, dtype=np.float64)
    d = (t - t.mean()) - (cur - cur.mean())
    d = np.convolve(np.pad(d, 1, mode="edge"), np.ones(3) / 3, mode="valid")
    d = np.clip(d * strength, -9, 9)
    S = librosa.stft(y, n_fft=1024, hop_length=256)
    f = librosa.fft_frequencies(sr=SR, n_fft=1024)
    g = np.ones_like(f)
    g[1:] = 10 ** (np.interp(np.log(f[1:]), np.log(BAND_CENTERS), d) / 20)
    return librosa.istft(S * g[:, None], hop_length=256, length=len(y)).astype(np.float32)


def _add_breath(y, hnr_user, hnr_synth, strength):
    """Foydalanuvchi ovozi havodorroq/xirillaroq bo'lsa, nozik aspiratsiya shovqini qo'shish."""
    if hnr_user is None or hnr_synth is None or strength <= 0:
        return y
    deficit = float(np.clip(hnr_synth - hnr_user, 0, 12))
    if deficit < 1.5:
        return y
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(len(y)).astype(np.float32)
    sos = butter(2, [1500, 7000], btype="band", fs=SR, output="sos")
    noise = sosfilt(sos, noise)
    env = np.convolve(np.abs(y), np.ones(441) / 441, mode="same")
    level_db = -38 + deficit * 1.6 * strength
    noise = noise / (np.std(noise) + 1e-9) * env * 10 ** (level_db / 20)
    return (y + noise).astype(np.float32)


def _normalize_level(y, target_db):
    m, db = _active_mask(y)
    cur = float(np.mean(db[m])) if m.any() else float(np.mean(db))
    g = 10 ** ((np.clip(target_db, -40, -12) - cur) / 20)
    y = y * min(g, 8.0)
    pk = np.max(np.abs(y)) + 1e-9
    if pk > 0.95:
        y = np.tanh(y / pk * 1.2) / np.tanh(1.2) * 0.95
    return y.astype(np.float32)


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text)
    parts = [p.strip() for p in parts if p and re.search(r"\w", p)]
    merged = []
    for p in parts:  # juda qisqa bo'laklarni oldingisiga qo'shish
        if merged and len(p) < 12:
            merged[-1] += " " + p
        else:
            merged.append(p)
    return merged[:MAX_SENTENCES]


# ───────────────────────────── Edge TTS ko'prigi ─────────────────────────────

_base_lock = threading.Lock()


def _edge(text, voice, rate_pct=0, pitch_hz=0, on_miss=None):
    import core
    o = core.opts({"voice": voice, "rate": rate_pct, "pitch": pitch_hz})
    return bytes(core.synth(text, o, on_miss=on_miss))


def _baseline(voice, tts_fn):
    """Edge ovozining 'tabiiy' f0 va tempi (bir marta o'lchanib keshlanadi)."""
    f = PROFILE_DIR / "_baseline.json"
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with _base_lock:
        data = json.loads(f.read_text()) if f.exists() else {}
        if voice in data:
            return data[voice]
        calib = ("Assalomu alaykum, bugun havo juda yaxshi. Men shaharga borib, "
                 "do'stlarim bilan uchrashaman va birga choy ichamiz.")
        try:
            y = decode_audio(tts_fn(calib, voice, 0, 0), ".mp3")
            a = analyze(np.tile(y, 2)) if len(y) / SR < 6 else analyze(y)
            data[voice] = {"f0": a["f0_median"], "art_rate": a["art_rate"], "f0_std_st": a["f0_std_st"]}
            f.write_text(json.dumps(data))
        except Exception:
            return {"f0": 115 if "Sardor" in voice else 205, "art_rate": 5.0, "f0_std_st": 3.0}
        return data[voice]


# ───────────────────────────── asosiy sintez ─────────────────────────────

def synthesize(text: str, pid: str, *, voice: str | None = None, engine: str = "auto",
               prosody: float = 1.0, match: float = 1.0, fmt: str = "mp3",
               on_miss=None, tts_fn=None) -> tuple[bytes, str, dict]:
    """Matnni profil ovozida sintez qiladi. Qaytaradi: (audio bytes, mimetype, info)."""
    _need_deps()
    text = (text or "").strip()
    if not text:
        raise ValueError("Matn kiriting.")
    if len(text) > MAX_CLONE_CHARS:
        raise ValueError(f"Matn uzun: {len(text)} belgi (maks. {MAX_CLONE_CHARS}).")
    prosody = float(np.clip(prosody, 0, 1.2))
    match = float(np.clip(match, 0, 1.2))
    tts_fn = tts_fn or _edge
    P = load_profile(pid)
    voice = voice or ("uz-UZ-SardorNeural" if P["gender_guess"] == "male" else "uz-UZ-MadinaNeural")
    t0 = time.time()
    info: dict = {"voice": voice}

    # 1) Edge uchun tempo va ohang oldindan sozlash
    base = _baseline(voice, tts_fn)
    rate = int(np.clip((P["art_rate"] / max(base["art_rate"], 1) - 1) * 100 * prosody, -35, 60))
    pitch = int(np.clip(0.6 * (P["f0_median"] - base["f0"]) * prosody, -50, 50))
    info.update(edge_rate=rate, edge_pitch=pitch)

    # 2) Jumlalar bo'yicha sintez
    sents = split_sentences(text)
    ys = [decode_audio(tts_fn(s, voice, rate, pitch, on_miss), ".mp3") for s in sents]
    joined = np.concatenate([np.pad(y, (0, int(0.2 * SR))) for y in ys])
    S = analyze(joined if len(joined) / SR >= 3 else np.tile(joined, 3))

    # 3) Prosodiya parametrlari
    pitch_ratio = (P["f0_median"] / max(S["f0_median"], 1)) ** prosody
    range_f = float(np.clip((P["f0_std_st"] / max(S["f0_std_st"], 0.5)) ** prosody, 0.5, 1.8))
    dur_f = float(np.clip((S["art_rate"] / max(P["art_rate"], 1)) ** prosody, 0.8, 1.25))
    fr = [P[k] / S[k] for k in ("f1", "f2", "f3") if P.get(k) and S.get(k)]
    formant = float(np.clip(np.mean(fr) if fr else 1.0, 0.82, 1.22) ** match)
    info.update(pitch_ratio=round(pitch_ratio, 3), range_factor=round(range_f, 2),
                dur_factor=round(dur_f, 2), formant_ratio=round(formant, 3))

    rnd = random.Random(zlib.crc32(text.encode()))
    pause = 0.35 + (min(max(P["pause_median"], 0.15), 1.4) - 0.35) * prosody

    def build(formant_ratio):
        parts = []
        for i, y in enumerate(ys):
            parts.append(_praat_adjust(y, pitch_ratio, range_f, dur_f, formant_ratio))
            if i < len(ys) - 1:
                parts.append(np.zeros(int(SR * pause * rnd.uniform(0.88, 1.12)), dtype=np.float32))
        pad = np.zeros(int(0.08 * SR), dtype=np.float32)
        return np.concatenate([pad] + parts + [pad])

    # 4) Tembr: neyron yoki yengil
    want = engine if engine in ("neural", "lite") else "auto"
    ok_neural, why = _Neural.status()
    used, eq_strength = "lite", 1.0 * match
    out = None
    if want in ("neural", "auto") and ok_neural:
        try:
            out = _Neural.convert(build(1.0), pid)
            used, eq_strength = "neural", 0.45 * match
        except Exception as exc:  # pragma: no cover
            info["neural_error"] = f"{type(exc).__name__}: {exc}"
    elif want == "neural":
        info["neural_error"] = why
    if out is None:
        out = build(formant)
    info["engine"] = used

    # 5) Spektr moslash, sifat, balandlik
    out = _eq_match(out, P["ltas"], eq_strength)
    out = _add_breath(out, P.get("hnr_db"), S.get("hnr_db"), match if used == "lite" else 0.5 * match)
    out = _normalize_level(out, P["rms_db"])
    data, mime = encode_audio(out, fmt)
    info["seconds"] = round(time.time() - t0, 1)
    return data, mime, info
