# 🎙️ Uzbekcha TTS — Free Uzbek Text-to-Speech Platform

<div align="center">

![Uzbekcha TTS Banner](https://raw.githubusercontent.com/developer-uzbek/tts-uzbek/main/static/banner.png)

**Free Uzbek Text-to-Speech — Natural Uzbek AI Voice Generator**  
*Tabiiy O'zbek Nutq Sintezi va MP3 Ovoz Generator*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![edge-tts](https://img.shields.io/badge/edge--tts-7.0%2B-brightgreen.svg)](https://github.com/rany2/edge-tts)
[![Status: Healthy](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](https://tts-uzbek.onrender.com/health)

[🌐 Website](https://tts-uzbek.onrender.com/) • [🤖 Telegram Bot](https://t.me/Uzbekcha_tts_bot) • [📖 API Guide](API.md) • [🤖 AI Agent Guide](AI_USAGE.md)

</div>

---

## 🌟 Overview

**Uzbekcha TTS** is a modern, production-grade text-to-speech platform focused on high-quality, natural-sounding speech synthesis for the Uzbek language. Powered by Microsoft Edge Neural AI voices, it delivers clean, expressive MP3 audio without subscription fees, usage limits, or forced sign-ups.

Whether you are an end user looking to listen to articles, a developer integrating speech synthesis into apps or bots, or an **autonomous AI agent (ChatGPT, Claude, Gemini, Perplexity)** generating and delivering real audio files, Uzbekcha TTS provides a unified, rock-solid solution.

---

## 🚀 Key Features

- **Natural Neural Voices**: Authentic Uzbek voices (`uz-UZ-SardorNeural` male, `uz-UZ-MadinaNeural` female) with clear intonation.
- **Multilingual Support**: Uzbek (`uz`), Russian (`ru`), English (`en`), Turkish (`tr`), Kazakh (`kk`), and 40+ additional languages.
- **Instant MP3 Delivery**: Direct streaming and downloadable audio binaries with proper `audio/mpeg` headers.
- **AI-Agent Ready**: Dedicated machine-readable discovery specifications (`llms.txt`, `llms-full.txt`, `openapi.yaml`, `ai-plugin.json`).
- **Production API**: Clean REST endpoints with JSON bodies or query parameters.
- **Telegram Inline Bot**: Generate speech directly in any Telegram chat via `@Uzbekcha_tts_bot text`.
- **Premium Responsive UI**: Elegant desktop and mobile layout with dark/light themes, waveform visualization, and client-side IndexedDB library.
- **Built-in Smart Cache**: In-memory LRU audio caching prevents redundant requests and ensures ultra-low latency.
- **Zero Lock-in**: Full CLI tool (`tts.py`) for offline or direct terminal conversion.

---

## 🎧 Quick Start & 5 Ways to Use

### 1. Web Studio
Visit [tts-uzbek.onrender.com](https://tts-uzbek.onrender.com/):
1. Enter your text (supports up to 100,000 characters with auto-chunking).
2. Choose voice (`Sardor` / `Madina`) and speech style (`Natural`, `Deep`, `Chipmunk`, `Hype`, `Calm`).
3. Press **Generate Voice** (`Ctrl + Enter`).
4. Play instantly and download your high-bitrate MP3.

### 2. Direct URL / Audio Tag
Stream MP3 directly from any browser or embed in HTML:
```text
https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo&voice=sardor
```

```html
<audio controls src="https://tts-uzbek.onrender.com/tts.mp3?q=Assalomu%20alaykum&voice=madina"></audio>
```

### 3. REST API
Generate audio programmatically via POST or GET:
```bash
curl -X POST https://tts-uzbek.onrender.com/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Salom, dunyo!","voice":"uz-UZ-SardorNeural","style":"natural"}' \
  -o output.mp3
```

### 4. Python & JavaScript SDK
```python
import requests

response = requests.post(
    "https://tts-uzbek.onrender.com/api/tts",
    json={"text": "Salom, dunyo!", "voice": "uz-UZ-SardorNeural"}
)

with open("output.mp3", "wb") as f:
    f.write(response.content)
```

```javascript
const fs = require('fs');
const res = await fetch("https://tts-uzbek.onrender.com/api/tts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "Salom!", voice: "madina" })
});
const buffer = Buffer.from(await res.arrayBuffer());
fs.writeFileSync("output.mp3", buffer);
```

### 5. Command Line (CLI)
```bash
# Direct terminal synthesis
python tts.py "Salom, dunyo!" -v sardor -o salom.mp3 --play

# From text file
python tts.py -f kitob.txt -v madina -o kitob.mp3
```

---

## 🤖 AI Assistant Integration

Uzbekcha TTS is built from the ground up to be discovered and executed by autonomous AI agents like **ChatGPT, Claude, Gemini, Perplexity, DeepSeek, and Grok**.

### The 8-Step Autonomous Delivery Workflow
When a user asks: *"Use Uzbekcha TTS to generate this Uzbek text and send me the MP3"*:

1. **Discovery**: Agent checks `https://tts-uzbek.onrender.com/llms.txt` or `openapi.yaml`.
2. **Voice Selection**: Reads `uz-UZ-SardorNeural` (male) or `uz-UZ-MadinaNeural` (female).
3. **Execution**: Issues `POST https://tts-uzbek.onrender.com/api/tts` with JSON body.
4. **Binary Retrieval**: Captures actual `audio/mpeg` response stream.
5. **Validation**: Verifies HTTP 200 and ID3 / MP3 audio header bytes.
6. **Local Persistence**: Saves file as `uzbekcha-tts-output.mp3`.
7. **File Attachment**: Attaches real binary MP3 to user conversation.
8. **Verified Fallback**: Provides direct download URL if platform attachments are unavailable.

👉 **Read the comprehensive technical guide: [AI_USAGE.md](AI_USAGE.md) and [AI_API_GUIDE.md](AI_API_GUIDE.md)**

---

## 🎙️ Available Uzbek Neural Voices

| Voice ID | Name | Gender | Language | Description |
|:---|:---|:---|:---|:---|
| `uz-UZ-SardorNeural` | Sardor | Male | Uzbek (`uz-UZ`) | Natural, clear, formal & conversational |
| `uz-UZ-MadinaNeural` | Madina | Female | Uzbek (`uz-UZ`) | Warm, expressive, melodic intonation |

*Full voice catalog across 40+ languages available at `GET /api/voices`.*

---

## 🛠️ Local Development & Self-Hosting

### Requirements
- Python 3.9 or higher
- `pip` package manager

### 1. Clone & Setup
```bash
git clone https://github.com/developer-uzbek/tts-uzbek.git
cd tts-uzbek
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables
Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

### 3. Run Locally
```bash
python combined_app.py
```
Open [http://localhost:5000](http://localhost:5000) in your browser.

### 4. Run Test Suite
```bash
python test_app.py
```

---

## ☁️ Deployment

### Render Deployment
This project includes pre-configured `render.yaml` and `Procfile`.
1. Fork or push this repository to GitHub.
2. In Render, select **New Web Service** connected to your repo.
3. Set Environment to **Python 3**, Build Command: `pip install -r requirements.txt`, Start Command: `python combined_app.py`.
4. Configure optional environment variables: `BOT_TOKEN`, `ADMIN_ID`, `PUBLIC_BASE_URL`.

---

## 🔒 Security, Privacy & Legal

- **Zero Data Retention**: Text is processed in volatile memory and never logged to persistent disks or external databases.
- **Rate Limiting**: Built-in rolling window IP throttling protects against DDoS and abusive spikes.
- **License**: Released under the permissive [MIT License](LICENSE).
- **Compliance**: Respects Microsoft Edge TTS terms and open-source standards. See [PRIVACY.md](PRIVACY.md) and [TERMS.md](TERMS.md).

---

## 🤝 Contributing

Contributions are warmly welcomed! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for pull request guidelines, test setup, and architecture standards.

---

<div align="center">

Crafted with ❤️ for the Uzbek language community and global developers.  
**Uzbekcha TTS — Free Uzbek Text-to-Speech Platform**

</div>
