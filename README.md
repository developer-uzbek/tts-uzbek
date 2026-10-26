# 🎙️ VoiceCraft Pro — bepul va cheksiz O'zbekcha TTS

Matnni tabiiy ovozga (MP3) aylantiradi. O'zbek, rus, turk, ingliz va Microsoft Edge Neural'dagi 40+ tilning barcha ovozlari.

| | |
|---|---|
| 🌐 Sayt | https://tts-uzbek.onrender.com/ |
| 🤖 Bot | https://t.me/Uzbekcha_tts_bot |

---

## Foydalanishning 5 usuli

### 1) Sayt
[tts-uzbek.onrender.com](https://tts-uzbek.onrender.com/) → matn yozing → ovoz va stilni tanlang → **Ovoz yaratish**.
Uzun matn avtomatik bo'laklanib, bitta MP3 ga ulanadi. Fayllar **sizning qurilmangizda** saqlanadi. Sayt tepasidagi rangli doiralar orqali **6 ta mavzu** tanlanadi. `Ctrl+Enter` — tezkor yaratish.

### 2) Telegram bot
[@Uzbekcha_tts_bot](https://t.me/Uzbekcha_tts_bot) ga matn yuboring — ovozli xabar qaytaradi. `/voice` — ovozni almashtirish, `/id` — o'z Telegram ID'ngiz.

### 3) Havola orqali — `?q=` yoki `?r=`
Saytning manziliga matnni yozing, shu zahoti MP3 qaytadi:

```text
https://tts-uzbek.onrender.com/?q=Salom, dunyo!
https://tts-uzbek.onrender.com/?r=Assalomu alaykum&voice=madina
https://tts-uzbek.onrender.com/?q=Привет&voice=ru&dl=1&name=privet
```

| Parametr | Ma'nosi | Misol |
|---|---|---|
| `q` yoki `r` (yoki `text`) | Matn | `?q=Salom` |
| `voice` | `sardor`, `madina`, `ahmet`, `dmitry`, `andrew` …, til kodi (`uz`, `ru`, `tr`, `en`) yoki to'liq ID | `voice=madina` |
| `style` | `natural`, `narrator`, `robot`, `minion`, `dramatic`, `whisper`, `cinematic` | `style=robot` |
| `rate` | Tezlik, % (−50…100) | `rate=20` |
| `pitch` | Ton, Hz (−50…50) | `pitch=-5` |
| `volume` | Balandlik, % | `volume=10` |
| `dl=1` | Brauzer ijro etmay, **yuklab olsin** | `dl=1` |
| `name` | Fayl nomi | `name=salom` |

Saytingizga qo'yish:

```html
<audio controls src="https://tts-uzbek.onrender.com/?q=Xush kelibsiz&voice=madina"></audio>
```

### 4) API (dasturlash uchun)
`GET` yoki `POST /api/tts` — javob: `audio/mpeg`. Ovozlar ro'yxati: `GET /api/voices`.

```bash
curl -X POST https://tts-uzbek.onrender.com/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Salom, dunyo!","voice":"sardor","style":"natural","rate":0,"pitch":0}' \
  -o salom.mp3
```

```python
import requests
r = requests.post("https://tts-uzbek.onrender.com/api/tts", json={"text": "Salom!", "voice": "madina"})
open("salom.mp3", "wb").write(r.content)
```

```js
const r = await fetch("https://tts-uzbek.onrender.com/api/tts", {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "Salom!", voice: "sardor" }),
});
const audio = new Audio(URL.createObjectURL(await r.blob())); audio.play();
```

Bitta so'rovda maksimal **5000 belgi** — uzunroq matnni bo'lib yuboring (sayt va `tts.py` buni o'zi qiladi). Bir xil so'rov keshdan darrov qaytadi. Server bepul tarifda ishlagani uchun bir IP'dan daqiqasiga 40 ta *yangi* matn qabul qilinadi (`429` bo'lsa biroz kuting).

### 5) CMD / PowerShell / terminal

**a) Kompyuterda ishlaydigan `tts.py` — Render'ga umuman yuk tushirmaydi (tavsiya)**

```powershell
pip install edge-tts
Invoke-WebRequest https://tts-uzbek.onrender.com/tts.py -OutFile tts.py    # yoki repodan oling

python tts.py "Salom, dunyo!"                              # -> tts.mp3
python tts.py "Salom" -v madina -o salom.mp3 --rate 10 --play
python tts.py -f kitob.txt -v sardor -o kitob.mp3          # fayldan (UTF-8), istalgan uzunlik
python tts.py --list uz                                    # ovozlar ro'yxati
```
`edge-tts` o'rnatilmagan bo'lsa, `tts.py` o'zi sayt API'siga o'tadi (`--api` — majburan shunday).

**b) Hech narsa o'rnatmasdan — PowerShell** (`curl` o'rniga `Invoke-WebRequest`):

```powershell
$t = [uri]::EscapeDataString("Salom, dunyo!")
Invoke-WebRequest "https://tts-uzbek.onrender.com/?q=$t&voice=madina" -OutFile salom.mp3
```

Doimiy buyruq qilish uchun `notepad $PROFILE` ga qo'shing:

```powershell
function tts($text, $out = "tts.mp3", $voice = "sardor") {
  Invoke-WebRequest ("https://tts-uzbek.onrender.com/?q=" + [uri]::EscapeDataString($text) + "&voice=$voice") -OutFile $out
  Start-Process $out
}
# keyin:  tts "Salom, dunyo!"
```

**c) CMD** (Windows 10+ da `curl.exe` bor):

```bat
curl -G "https://tts-uzbek.onrender.com/" --data-urlencode "q=Salom, dunyo!" -d voice=sardor -o salom.mp3
```

---

## Render'ga joylash

Repo GitHub'da, Render'da **Web Service** (Python). Start buyrug'i: `python combined_app.py`. **Environment** bo'limida:

| O'zgaruvchi | Vazifasi |
|---|---|
| `BOT_TOKEN` | @BotFather bergan token |
| `ADMIN_ID` | Admin Telegram ID. Bir nechta bo'lsa vergul bilan: `123456, 789012`. ID'ni bilish uchun botga `/id` yozing |
| `PUBLIC_BASE_URL` | Sayt manzili (standart: `https://tts-uzbek.onrender.com`) |
| `BOT_USERNAME` | Bot username'i (standart: `Uzbekcha_tts_bot`) |
| `TELEGRAM_CHANNEL` | *Ixtiyoriy.* Boshlang'ich majburiy-obuna kanali. Keyin admin paneldan boshqariladi |
| `MAX_CHARS` · `RATE_PER_MIN` · `CACHE_MB` · `MAX_JOBS` | *Ixtiyoriy.* Bitta so'rov uzunligi (5000) · IP uchun daqiqalik limit (40, `0` = o'chiq) · kesh hajmi (24 MB) · bir vaqtdagi sintezlar (4) |

Lokal ishga tushirish: `pip install -r requirements.txt && python combined_app.py` → http://localhost:5000. Tekshiruv: `python test_app.py`.

---

## 🛠 Bot admini

`ADMIN_ID` dagi akkaunt botga `/admin` yozadi:

- **📢 Post yuborish** — matn yoki rasm (izoh bilan) yuboring → ko'rib chiqing → *Yuborish*. Barcha foydalanuvchilarga boradi; botni bloklaganlar ro'yxatdan avtomatik chiqariladi.
- **🔒 Majburiy obuna** — yoqish / o'chirish, kanal qo'shish va olib tashlash (bir nechta kanal mumkin). Bot kanalda **admin** bo'lishi shart — qo'shishda bot buni o'zi tekshiradi.
- **⏸ To'xtatish** — 10 daqiqa, 1 soat, 6 soat, 1 kun, 7 kun yoki o'zingiz yozgan vaqt (`45 daqiqa`, `3 soat`, `2 kun`). Vaqt tugagach bot o'zi ochiladi. Tezkor: `/pause 2h`, `/pause 0` (davom ettirish). Adminlar to'xtatilgan botdan ham foydalana oladi.
- **📊 Statistika** — jami, bugun qo'shilgan, bugun va 7 kunda faol foydalanuvchilar.

**Baza yo'q.** Foydalanuvchilar `state.json` da saqlanadi (har biri ~25 bayt — 10 000 ta foydalanuvchi ≈ 250 KB). Render bepul tarifda fayllar qayta deploy'da o'chgani uchun, o'zgarish bo'lsa bot har 6 soatda (eng ko'pi bilan) shu faylni adminga jim yuboradi va pin qiladi; qayta ishga tushganda ro'yxatni o'sha fayldan o'zi tiklaydi. Qo'lda tiklash — faylni botga yuborish.

---

## Fayllar

`index.html` — sayt · `combined_app.py` — server va API · `core.py` — TTS yadrosi va kesh · `bot.py` — bot va admin · `tts.py` — terminal uchun · `test_app.py` — tekshiruv

Ovozlar Microsoft Edge Neural TTS'dan olinadi ([edge-tts](https://github.com/rany2/edge-tts)).
