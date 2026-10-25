# 🎙️ Infinite AI TTS Generator

Ushbu loyiha cheksiz AI text-to-speech generatsiyasini quyidagi 4 usul bilan taqdim etadi:

1. Veb-sayt orqali
2. Telegram bot orqali
3. API orqali
4. CMD / PowerShell / CLI orqali

Loyiha Microsoft Edge Neural TTS dan foydalanadi. Foydalanuvchilar mening saytim, botim, API'im yoki PowerShell/CMD orqali cheksiz audio fayllarini yaratishi mumkin.

---

## 1) Veb-sayt orqali ishlatish

Saytga kirib matnni yozing, ovoz turini tanlang, stilni tanlang va `Generate` tugmasini bosing.

- Mavjud ovozlar: Sardor, Madina, Ahmet, Dmitry, Alex
- Mavjud stil: Robot, Minion, Narrator, Dramatic, Whisper, Cinematic
- MP3 fayl avtomatik tarzda yuklab olinadi

## 2) Telegram bot orqali ishlatish

Botga matn yuboring. Agar `SUBSCRIBE_REQUIRED=true` bo'lsa, kanalga obuna bo'lish shart bo'ladi.

Environment variable:

```bash
BOT_TOKEN=your_telegram_token
SUBSCRIBE_REQUIRED=true
TELEGRAM_CHANNEL=@tgchannel
```

Botdan foydalanish:

- `/start` buyrug'i
- matn yuborish
- kerakli ovozni tanlash

## 3) API orqali ishlatish

Base URL:

```bash
https://your-host-url/api/tts
```

POST so'rovi:

```bash
curl -X POST "https://your-host-url/api/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Salom, bu mening TTS sinovim!",
    "voice": "en-US-AlexNeural",
    "style": "robot",
    "filename": "my_voice_file"
  }'
```

Yoki GET orqali:

```bash
https://your-host-url/api/tts?text=Salom%20bu%20mening%20TTS%20sinovim&voice=en-US-AlexNeural&style=robot&filename=my_voice_file
```

Bu linkdan MP3 audio fayl qaytariladi.

## 4) CMD / PowerShell / CLI orqali ishlatish

Bu usul orqali matnni linkga qo'shib yoki parametr sifatida yuborish imkoniyati mavjud.

### PowerShell misoli

```powershell
$base = "https://your-host-url/api/tts"
$text = "Salom, men PowerShell orqali audio yaratmoqdaman."
$encoded = [System.Web.HttpUtility]::UrlEncode($text)
$url = "$base?text=$encoded&voice=en-US-AlexNeural&style=minion&filename=power_tts"
Invoke-WebRequest -Uri $url -OutFile "power_tts.mp3"
```

### CMD misoli

```cmd
curl -L "https://your-host-url/api/tts?text=Salom%20bu%20mening%20cmd%20sinovim&voice=en-US-AlexNeural&style=robot&filename=cmd_tts" -o cmd_tts.mp3
```

### Python CLI misoli

```bash
python -c "import requests; r=requests.get('https://your-host-url/api/tts', params={'text':'Salom bu python dan','voice':'en-US-AlexNeural','style':'dramatic','filename':'python_tts'}); open('python_tts.mp3','wb').write(r.content)"
```

---

## Qisqa ishlatish ko'rsatmasi

- Sayt: `https://your-host-url/`
- Health tekshirish: `https://your-host-url/health`
- Ovozlar ro'yxati: `https://your-host-url/api/voices`

## Muhit o'zgaruvchilari

```bash
BOT_TOKEN=your_telegram_token
SUBSCRIBE_REQUIRED=true
TELEGRAM_CHANNEL=@tgchannel
PORT=5000
```

## Xavfsizlik va ishlatish

- Cheksiz TTS generatsiyasi sayt, API, bot va shell orqali ishlatilishi mumkin.
- Majburiy kanal obunasini yoqish mumkin.
- Har bir xatolikni `health` endpoint orqali tekshirish mumkin.

## Loyiha maqsadi

Loyiha foydalanuvchiga 4 xil yondashuvdan birini tanlash imkonini beradi:

- oddiy saytdan foydalanish
- Telegram botdan foydalanish
- backend API orqali audio yaratish
- command shell orqali tez audio yaratish

Shunday qilib, odamlar sizning linkingiz, botingiz yoki saytingiz orqali cheksiz TTS ishlatishi mumkin.
