#!/usr/bin/env python3
"""tts.py — Convert text to MP3 from the command line.

Usage:
  pip install edge-tts          (one-time; falls back to API if not installed)
  python tts.py "Salom, dunyo!"
  python tts.py -f kitob.txt -v madina -o kitob.mp3 --rate 10 --play
  python tts.py "Привет" -l ru -g female
  python tts.py "Hello" -v en-male
  echo Salom | python tts.py -
  python tts.py --list uz
"""
import argparse, asyncio, json, os, re, subprocess, sys, urllib.error, urllib.request

API = os.environ.get("TTS_API", "https://tts-uzbek.onrender.com").rstrip("/")
PAIRS = {
    "uz": ("uz-UZ-SardorNeural", "uz-UZ-MadinaNeural"),
    "ru": ("ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural"),
    "en": ("en-US-AndrewNeural", "en-US-AriaNeural"),
    "tr": ("tr-TR-AhmetNeural", "tr-TR-EmelNeural"),
    "kk": ("kk-KZ-DauletNeural", "kk-KZ-AigulNeural"),
}
NAMES = {n.lower(): i for p in PAIRS.values() for i in p for n in [i.split("-")[2][:-6]]}
MALE = {"male", "m", "man", "erkak"}
FEMALE = {"female", "f", "woman", "ayol"}

try:
    import edge_tts
except ImportError:
    edge_tts = None


def local_voice(voice, lang, gender):
    """Resolve voice ID for local usage: name, language, language-gender, or full ID."""
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
        sys.exit(f"Voice not found: {voice or lang}. List: python tts.py --list")
    return sorted(c, key=lambda x: x["ShortName"])[0]["ShortName"]


def chunks(text, size=3000):
    out, cur = [], ""
    for s in re.sub(r"([.!?…])\s+", r"\1\n", text).split("\n"):
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
        sys.exit("Error: " + json.loads(e.read() or b"{}").get("message", str(e)))
    except urllib.error.URLError as e:
        sys.exit(f"Cannot connect to server ({e.reason}). The Render service may be sleeping — try again in 1 minute.")


def main():
    a = argparse.ArgumentParser(description="Uzbekcha TTS — Text to MP3 (free)")
    a.add_argument("text", nargs="*", help="text to convert, or '-' for stdin")
    a.add_argument("-f", "--file", help="text file (UTF-8)")
    a.add_argument("-o", "--out", default="uzbekcha-tts-output.mp3")
    a.add_argument("-v", "--voice", help="name (sardor, madina, dmitry...), 'ru-female', or full ID")
    a.add_argument("-l", "--lang", help="language: uz, ru, en, tr, kk, de, fr ...")
    a.add_argument("-g", "--gender", help="male / female")
    a.add_argument("--rate", type=int, default=0, help="speed, %% (-50..100)")
    a.add_argument("--pitch", type=int, default=0, help="pitch, Hz (-50..50)")
    a.add_argument("--style", default="natural")
    a.add_argument("--api", action="store_true", help="force using the web API instead of local edge-tts")
    a.add_argument("--play", action="store_true", help="open the file after generation")
    a.add_argument("--list", nargs="?", const="", metavar="LANG", help="list voices (e.g.: uz)")
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
        sys.exit('Enter text. Example: python tts.py "Salom, dunyo!"')

    if local:
        voice = local_voice(n.voice, n.lang, n.gender)
        asyncio.run(edge_tts.Communicate(text, voice, rate=f"{n.rate:+d}%", pitch=f"{n.pitch:+d}Hz").save(n.out))
    else:
        parts = chunks(text)
        with open(n.out, "wb") as f:
            for i, p in enumerate(parts, 1):
                print(f"[{i}/{len(parts)}] generating...", file=sys.stderr)
                f.write(call("/api/tts", {"text": p, "voice": n.voice, "lang": n.lang, "gender": n.gender, "rate": n.rate, "pitch": n.pitch, "style": n.style}))
    print(f"OK: {n.out} ({os.path.getsize(n.out) // 1024} KB)")
    if n.play:
        if os.name == "nt":
            os.startfile(n.out)
        else:
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", n.out])


if __name__ == "__main__":
    main()
