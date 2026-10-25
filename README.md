# 🎙️ Infinite AI TTS Generator

Ushbu loyiha cheksiz AI text-to-speech generatsiyasini quyidagi 4 usul bilan taqdim etadi:

1. Veb-sayt orqali
2. Telegram bot orqali
3. API orqali
4. CMD / PowerShell / CLI orqali

Website: https://tts-uzbek.onrender.com/
Telegram bot: https://t.me/Uzbekcha_tts_bot

Loyiha Microsoft Edge Neural TTS dan foydalanadi. Foydalanuvchilar saytdan, botdan, API orqali yoki PowerShell/CMD orqali audio fayllarini yaratishi mumkin.

---

## 1) Veb-sayt orqali ishlatish

Saytga kirib matnni yozing, ovoz turini tanlang, stilni tanlang va `Generate` tugmasini bosing.

Sayt manzili:

```text
https://tts-uzbek.onrender.com/
```

- Mavjud ovozlar: Sardor, Madina, Ahmet, Dmitry, Alex
- Mavjud stil: Robot, Minion, Narrator, Dramatic, Whisper, Cinematic
- MP3 fayl avtomatik tarzda yuklab olinadi

---

## 2) Telegram bot orqali ishlatish

Botga matn yuboring:

```text
https://t.me/Uzbekcha_tts_bot
```

Botdan foydalanish:

- `/start` buyrug'i
- matn yuborish
- ovozni o'zgartirish uchun `/voice`

---

## 3) API orqali ishlatish

Base URL:

```text
https://tts-uzbek.onrender.com
```

### POST so'rovi

```bash
curl -X POST "https://tts-uzbek.onrender.com/api/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Salom, bu mening TTS sinovim!",
    "voice": "en-US-AlexNeural",
    "style": "robot",
    "filename": "my_voice_file"
  }'
```

### GET so'rovi

```bash
curl -L "https://tts-uzbek.onrender.com/api/tts?text=Salom%20bu%20mening%20TTS%20sinovim&voice=en-US-AlexNeural&style=robot&filename=my_voice_file" -o my_voice_file.mp3
```

Yoki browser orqali:

```text
https://tts-uzbek.onrender.com/api/tts?text=Salom%20bu%20mening%20TTS%20sinovim&voice=en-US-AlexNeural&style=robot&filename=my_voice_file
```

Bu linkdan MP3 audio fayl qaytariladi.

---

## 4) CMD / PowerShell / CLI orqali ishlatish

### PowerShell misoli

```powershell
$base = "https://tts-uzbek.onrender.com/api/tts"
$text = "Salom, men PowerShell orqali audio yaratmoqdaman."
$encoded = [System.Web.HttpUtility]::UrlEncode($text)
$url = "$base?text=$encoded&voice=en-US-AlexNeural&style=minion&filename=power_tts"
Invoke-WebRequest -Uri $url -OutFile "power_tts.mp3"
```

### CMD misoli

```cmd
curl -L "https://tts-uzbek.onrender.com/api/tts?text=Salom%20bu%20mening%20cmd%20sinovim&voice=en-US-AlexNeural&style=robot&filename=cmd_tts" -o cmd_tts.mp3
```

### Python CLI misoli

```bash
python -c "import requests; r=requests.get('https://tts-uzbek.onrender.com/api/tts', params={'text':'Salom bu python dan','voice':'en-US-AlexNeural','style':'dramatic','filename':'python_tts'}); open('python_tts.mp3','wb').write(r.content)"
```

---

## Qisqa ishlatish ko'rsatmasi

- Sayt: `https://tts-uzbek.onrender.com/`
- Health: `https://tts-uzbek.onrender.com/health`
- Ovozlar ro'yxati: `https://tts-uzbek.onrender.com/api/voices`
- Telegram bot: `https://t.me/Uzbekcha_tts_bot`

---

## Muhit o'zgaruvchilari

```bash
PUBLIC_BASE_URL=https://tts-uzbek.onrender.com
PORT=5000
```

---

## Xavfsizlik va ishlatish

- Cheksiz TTS generatsiyasi sayt, API, bot va shell orqali ishlatilishi mumkin.
- Majburiy kanal obunasini yoqish mumkin.
- Har bir xatolikni `health` endpoint orqali tekshirish mumkin.
- Barcha API so'rovlar sayt manzili bilan ishlaydi: `https://tts-uzbek.onrender.com`

---

## Loyiha maqsadi

Loyiha foydalanuvchiga 4 xil yondashuvdan birini tanlash imkonini beradi:

- oddiy saytdan foydalanish
- Telegram botdan foydalanish
- backend API orqali audio yaratish
- command shell orqali tez audio yaratish

Shunday qilib, odamlar sizning sayt, bot yoki API orqali cheksiz TTS ishlatishi mumkin.
