#!/usr/bin/env python3
"""tts.py — CMD / PowerShell / terminaldan matnni MP3 ga aylantiradi.

  pip install edge-tts          (bir marta; o'rnatilmasa sayt API'si ishlatiladi)
  python tts.py "Salom, dunyo!"
  python tts.py -f kitob.txt -v madina -o kitob.mp3 --rate 10 --play
  python tts.py "Привет" -l ru -g female          (til + jins)
  python tts.py "Hello" -v en-male
  echo Salom | python tts.py -
  python tts.py --list uz
"""
import argparse, asyncio, json, os, re, subprocess, sys, urllib.error, urllib.request

API = os.environ.get("TTS_API", "https://tts-uzbek.onrender.com").rstrip("/")
PAIRS = {"uz": ("uz-UZ-SardorNeural", "uz-UZ-MadinaNeural"), "ru": ("ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural"),
         "en": ("en-US-AndrewNeural", "en-US-AriaNeural"), "tr": ("tr-TR-AhmetNeural", "tr-TR-EmelNeural"),
         "kk": ("kk-KZ-DauletNeural", "kk-KZ-AigulNeural")}   # (erkak, ayol)
NAMES = {n.lower(): i for p in PAIRS.values() for i in p for n in [i.split("-")[2][:-6]]}
MALE = {"male", "m", "man", "erkak"}
FEMALE = {"female", "f", "woman", "ayol"}

try:
    import edge_tts
except ImportError:
    edge_tts = None


def local_voice(voice, lang, gender):
    """Kompyuterda ishlaganda ovoz ID: ism (madina), til (ru), til-jins (uz-female) yoki to'liq ID."""
    v = (voice or "").strip()
    if re.fullmatch(r"[a-z]{2,3}-[A-Za-z0-9]+-[A-Za-z0-9-]+Neural", v):
        return v
    if v.lower() in NAMES:
        return NAMES[v.lower()]
    p = [x for x in re.split(r"[-_ ]+", v.lower()) if x]
    lang = (lang or (p[0] if p else "uz")).lower()
    g = (gender or next((x for x in p[1:] if x in MALE | FEMALE), "")).lower()
    if lang in PAIRS:
        return PAIRS[lang][g in FEMALE]
    vs = asyncio.run(edge_tts.list_voices())
    c = [x for x in vs if x["Locale"].lower().startswith(lang) or x["ShortName"].lower().endswith(f"-{lang}neural")]
    c = [x for x in c if x["Gender"] == ("Female" if g in FEMALE else "Male")] or c
    if not c:
        sys.exit(f"Ovoz topilmadi: {voice or lang}. Ro'yxat: python tts.py --list")
    return sorted(c, key=lambda x: x["ShortName"])[0]["ShortName"]


def chunks(text, size=3000):
    out, cur = [], ""
    for s in re.sub(r"([.!?...])\s+", r"\1\n", text).split("\n"):
        while len(s) > size:
            out.append(s[:size]); s = s[size:]
        if len(cur) + len(s) + 1 > size and cur:
            out.append(cur); cur = ""
        cur += s + " "
    return out + [cur] if cur.strip() else out


def call(path, body=None):
    req = urllib.request.Request(API + path, json.dumps(body).encode() if body else None, {"Content-Type": "application/json"})
    try:
        return urllib.request.urlopen(req, timeout=120).read()
    except urllib.error.HTTPError as e:
        sys.exit("Xato: " + json.loads(e.read() or b"{}").get("message", str(e)))
    except urllib.error.URLError as e:
        sys.exit(f"Server bilan aloqa yo'q ({e.reason}). Render uxlab yotgan bo'lishi mumkin - 1 daqiqadan so'ng qayta urinib ko'ring.")


def main():
    a = argparse.ArgumentParser(description="Matn -> MP3 (bepul, cheksiz)")
    a.add_argument("text", nargs="*", help="matn, yoki '-' (stdin)")
    a.add_argument("-f", "--file", help="matn fayli (UTF-8)")
    a.add_argument("-o", "--out", default="tts.mp3")
    a.add_argument("-v", "--voice", help="ism (sardor, madina, dmitry...), 'ru-female' yoki to'liq ID")
    a.add_argument("-l", "--lang", help="til: uz, ru, en, tr, kk, de, fr ...")
    a.add_argument("-g", "--gender", help="male / female (erkak / ayol)")
    a.add_argument("--rate", type=int, default=0, help="tezlik, %% (-50..100)")
    a.add_argument("--pitch", type=int, default=0, help="ton, Hz (-50..50)")
    a.add_argument("--style", default="natural")
    a.add_argument("--api", action="store_true", help="kompyuterda emas, sayt API'si orqali")
    a.add_argument("--play", action="store_true", help="tayyor bo'lgach ochish")
    a.add_argument("--list", nargs="?", const="", metavar="TIL", help="ovozlar ro'yxati (masalan: uz)")
    n = a.parse_args()

    local = edge_tts is not None and not n.api
    if n.list is not None:
        if local:
            vs = [(v["ShortName"], v["Gender"]) for v in asyncio.run(edge_tts.list_voices())]
        else:
            vs = [(v["id"], v["gender"]) for v in json.loads(call("/api/voices"))["voices"]]
        return print("\n".join(f"{i}  {g}" for i, g in vs if i.lower().startswith(n.list.lower())))

    if n.file:
        text = open(n.file, encoding="utf-8-sig").read()
    elif n.text == ["-"] or (not n.text and not sys.stdin.isatty()):
        text = sys.stdin.buffer.read().decode("utf-8-sig")
    else:
        text = " ".join(n.text)
    text = text.strip()
    if not text:
        sys.exit('Matn kiriting. Masalan: python tts.py "Salom, dunyo!"')

    if local:
        voice = local_voice(n.voice, n.lang, n.gender)
        asyncio.run(edge_tts.Communicate(text, voice, rate=f"{n.rate:+d}%", pitch=f"{n.pitch:+d}Hz").save(n.out))
    else:
        parts = chunks(text)
        with open(n.out, "wb") as f:
            for i, p in enumerate(parts, 1):
                print(f"[{i}/{len(parts)}] yaratilmoqda...", file=sys.stderr)
                f.write(call("/api/tts", {"text": p, "voice": n.voice, "lang": n.lang, "gender": n.gender, "rate": n.rate, "pitch": n.pitch, "style": n.style}))
    print(f"OK: {n.out} ({os.path.getsize(n.out) // 1024} KB)")
    if n.play:
        if os.name == "nt":
            os.startfile(n.out)
        else:
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", n.out])


if __name__ == "__main__":
    main()
