# 🎙️ Bepul va Cheksiz AI Text-to-Speech (Web Sayt + Telegram Bot)

Ushbu loyiha **Render.com** va **GitHub** uchun 100% tayyor holatga keltirilgan bo'lib, bir vaqtning o'zida ham **Veb-sayt**ni, ham **Telegram Bot**ni mutlaqo bepul (kartasiz) ishlatish imkonini beradi.

---

## 📁 Loyiha Tarkibi:
* `combined_app.py` — Bosh server (Sayt va Telegram Botni parallel boshqaradi)
* `index.html` va `public/index.html` — Zamonaviy Glassmorphism UI (CSS va JS ichida)
* `render.yaml` — Render.com uchun avtomatik 1-bosishda sozlash fayli
* `Procfile` — Render server ishga tushirish buyrug'i
* `requirements.txt` — Barcha kerakli Python kutubxonalari
* `.gitignore` — Keraksiz fayllarni GitHub'ga chiqarmaslik uchun

---

## 🚀 Render.com'ga Joylash (3 Bosqichda, 100% Kartasiz):

### 1-Qadam: GitHub'ga yuklash
1. [github.com](https://github.com) ga kiring va yangi bo'sh repozitoriy yarating (masalan, `ai-tts-studio`).
2. Ushbu papkadagi barcha fayllarni yangi ochilgan repozitoriyga yuklang (`Upload files` yoki Git orqali `git push`).

### 2-Qadam: Telegram Bot Tokenini olish (Ixtiyoriy)
* Agar Telegram Bot ham ishlashini xohlasangiz:
1. Telegramda **[@BotFather](https://t.me/BotFather)** ga kiring.
2. `/newbot` buyrug'ini yozing va botingizga nom bering.
3. BotFather sizga bergan **Token**ni nusxalab oling.

### 3-Qadam: Render.com'da 1 ta bosishda yoqish
1. [render.com](https://render.com) ga kiring va **"Sign in with GitHub"** orqali kiring (Bank kartasi so'ramaydi).
2. **"New +" ➔ "Web Service"** tugmasini bosing.
3. GitHub'dagi `ai-tts-studio` repozitoriyangizni tanlang.
4. Render avtomatik ravishda barcha sozlamalarni aniqlaydi:
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `python combined_app.py`
   * **Instance Type:** `Free` ($0)
5. **"Environment Variables"** bo'limida yangi o'zgaruvchi qo'shing:
   * Key: `BOT_TOKEN`
   * Value: `BotFather'dan olgan tokeningiz` *(agar faqat sayt kerak bo'lsa, buni bo'sh qoldirishingiz mumkin)*
6. **"Deploy Web Service"** tugmasini bosing!

---

## ⚡ Serverni 24/7 Doimiy Ishlatish (Uxlatmaslik):
Render bepul tarifi 15 daqiqa murojaat bo'lmasa uyquga ketmasligi uchun:
1. [cron-job.org](https://cron-job.org) ga kiring (100% bepul).
2. Yangi cron job qo'shing: `https://sizning-saytingiz.onrender.com/health`
3. Intervalni **har 10 daqiqaga** qo'ying.

Shunda serveringiz hech qachon to'xtamaydi va yillab uzluksiz ishlaydi!
