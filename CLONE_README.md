# 🧬 Mening ovozim — ovoz klonlash (localhost)

## 1. Yengil rejim (darhol ishlaydi)
```bash
pip install -r requirements-clone.txt
# ffmpeg kerak:  Windows: winget install ffmpeg | Mac: brew install ffmpeg | Linux: sudo apt install ffmpeg
python combined_app.py
```
Brauzerda oching: **http://localhost:5000/clone**

1. Matnni o'qib 45–60 soniya yozing (yoki fayl yuklang), rozilik belgisini qo'ying → **Tahlil qilish**
2. "Ovoz DNK'ngiz" kartalarini ko'ring
3. Matn kiriting → **Mening ovozimda yaratish**

## 2. Neyron rejim (OpenVoice V2 — ancha o'xshash)
```bash
pip install -r requirements-clone-neural.txt
pip install --no-deps git+https://github.com/myshell-ai/OpenVoice.git
```
Model fayllarini yuklab, loyiha ildizida `checkpoints_v2/` papkasiga oching
(ichida `converter/config.json` va `converter/checkpoint.pth` bo'lishi kerak):
- https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip
  (yoki HuggingFace: `myshell-ai/OpenVoiceV2`)

Serverni qayta ishga tushiring — sahifa tepasida "Neyron: tayyor" chiqadi.

## Qanday ishlaydi
Edge Neural (Sardor/Madina) → o'zbekcha talaffuz → **prosodiya** (ohang, intonatsiya, tempo, pauza: Praat) →
**tembr** (OpenVoice yoki formant+EQ) → **sifat** (HNR/havodorlik, energiya).

## Muhim
- Faqat o'z ovozingiz yoki egasining roziligi bilan.
- Profillar `voice_profiles/` da (faqat sizning kompyuteringizda). Internetga ochishdan oldin autentifikatsiya qo'shing.
- Atrof-muhit: `CLONE_DIR`, `OPENVOICE_CKPT`, `MAX_CLONE_CHARS`.
