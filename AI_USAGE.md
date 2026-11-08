# AI Integration Guide — Uzbekcha TTS

> **For AI Assistants, LLM Agents, and Automated Systems**
>
> This guide explains how an AI assistant can discover, use, and integrate
> the Uzbekcha TTS (Text-to-Speech) service to generate audio from text.

---

## Table of Contents

- [1. Service Discovery](#1-service-discovery)
- [2. Listing Available Voices](#2-listing-available-voices)
- [3. Generating Audio from Text](#3-generating-audio-from-text)
- [4. Downloading and Saving the MP3 File](#4-downloading-and-saving-the-mp3-file)
- [5. Returning Audio to Users](#5-returning-audio-to-users)
- [6. Error Handling](#6-error-handling)
- [7. Verifying Audio Validity](#7-verifying-audio-validity)
- [8. Complete Workflow Example](#8-complete-workflow-example)
- [9. Important Limitations for AI Assistants](#9-important-limitations-for-ai-assistants)

---

## 1. Service Discovery

Before generating audio, an AI assistant should discover the service and its capabilities.

### Step 1a: Check the Service Info Endpoint

The `/api/info` endpoint returns machine-readable metadata about the service:

**cURL:**

```bash
curl https://tts-uzbek.onrender.com/api/info
```

**Python:**

```python
import requests

response = requests.get("https://tts-uzbek.onrender.com/api/info")
info = response.json()
print(info)
```

**JavaScript:**

```javascript
const response = await fetch("https://tts-uzbek.onrender.com/api/info");
const info = await response.json();
console.log(info);
```

### Step 1b: Check Service Health

Verify the service is online before attempting to generate audio:

```bash
curl https://tts-uzbek.onrender.com/health
```

A `200 OK` response means the service is ready.

### Step 1c: AI Plugin and OpenAPI Discovery

The service also provides standard AI discovery files:

| File | URL | Purpose |
|------|-----|---------|
| `llms.txt` | `https://tts-uzbek.onrender.com/llms.txt` | Plain-text summary for LLMs |
| `ai-plugin.json` | `https://tts-uzbek.onrender.com/.well-known/ai-plugin.json` | ChatGPT/OpenAI plugin manifest |
| OpenAPI Spec | `https://tts-uzbek.onrender.com/openapi.json` | Full API specification |

---

## 2. Listing Available Voices

Before generating audio, list the available voices to choose the right one for the user's language and preference.

### Request

```bash
curl https://tts-uzbek.onrender.com/api/voices
```

### Python Example

```python
import requests

response = requests.get("https://tts-uzbek.onrender.com/api/voices")
data = response.json()

for voice in data.get("voices", []):
    print(f"{voice['name']} — {voice['locale']} ({voice['gender']})")
```

### JavaScript Example

```javascript
const response = await fetch("https://tts-uzbek.onrender.com/api/voices");
const data = await response.json();

data.voices.forEach(voice => {
    console.log(`${voice.name} — ${voice.locale} (${voice.gender})`);
});
```

### Default Voice Reference

| Language | Male Voice | Female Voice |
|----------|-----------|--------------|
| Uzbek (uz) | `uz-UZ-SardorNeural` (Sardor) | `uz-UZ-MadinaNeural` (Madina) |
| Russian (ru) | `ru-RU-DmitryNeural` (Dmitry) | `ru-RU-SvetlanaNeural` (Svetlana) |
| English (en) | `en-US-AndrewNeural` (Andrew) | `en-US-AriaNeural` (Aria) |
| Turkish (tr) | `tr-TR-AhmetNeural` (Ahmet) | `tr-TR-EmelNeural` (Emel) |
| Kazakh (kk) | `kk-KZ-DauletNeural` (Daulet) | `kk-KZ-AigulNeural` (Aigul) |

### Voice Selection Methods

You can select a voice in several ways:

| Method | Example | Description |
|--------|---------|-------------|
| Full ID | `voice=uz-UZ-SardorNeural` | Exact voice identifier |
| Short name | `voice=sardor` | Case-insensitive name match |
| Language code | `lang=uz` | Uses default voice for that language |
| Language + Gender | `voice=uz-female` | Combines language and gender |
| Separate params | `lang=uz&gender=female` | Explicit language and gender |

---

## 3. Generating Audio from Text

This is the core operation: converting text into spoken audio (MP3).

> **Key concept:** Generating audio means sending text to the API and receiving
> binary MP3 data in the response. The audio is streamed back — it is not stored
> on a permanent URL.

### Method A: Query Parameter (Simplest)

**cURL:**

```bash
curl -o speech.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo&voice=sardor"
```

**Python:**

```python
import requests

response = requests.get(
    "https://tts-uzbek.onrender.com/tts.mp3",
    params={
        "q": "Salom dunyo",
        "voice": "sardor"
    }
)

if response.status_code == 200:
    with open("speech.mp3", "wb") as f:
        f.write(response.content)
    print("Audio saved to speech.mp3")
else:
    print(f"Error: {response.status_code} — {response.text}")
```

**JavaScript (Node.js):**

```javascript
import fs from "fs";

const params = new URLSearchParams({ q: "Salom dunyo", voice: "sardor" });
const response = await fetch(`https://tts-uzbek.onrender.com/tts.mp3?${params}`);

if (response.ok) {
    const buffer = Buffer.from(await response.arrayBuffer());
    fs.writeFileSync("speech.mp3", buffer);
    console.log("Audio saved to speech.mp3");
} else {
    console.error(`Error: ${response.status}`);
}
```

### Method B: JSON API (Recommended for AI Agents)

**cURL:**

```bash
curl -X POST "https://tts-uzbek.onrender.com/api/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Salom dunyo", "voice": "sardor", "style": "natural", "rate": 0, "pitch": 0}' \
  -o speech.mp3
```

**Python:**

```python
import requests

response = requests.post(
    "https://tts-uzbek.onrender.com/api/tts",
    json={
        "text": "Salom dunyo",
        "voice": "sardor",
        "style": "natural",
        "rate": 0,
        "pitch": 0
    }
)

if response.status_code == 200:
    with open("speech.mp3", "wb") as f:
        f.write(response.content)
    print("Audio generated and saved successfully")
else:
    print(f"Error: {response.status_code} — {response.text}")
```

**JavaScript (Node.js):**

```javascript
import fs from "fs";

const response = await fetch("https://tts-uzbek.onrender.com/api/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        text: "Salom dunyo",
        voice: "sardor",
        style: "natural",
        rate: 0,
        pitch: 0
    })
});

if (response.ok) {
    const buffer = Buffer.from(await response.arrayBuffer());
    fs.writeFileSync("speech.mp3", buffer);
    console.log("Audio generated and saved successfully");
} else {
    console.error(`Error: ${response.status}`);
}
```

### Available Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` / `text` | string | *(required)* | Text to convert to speech (max 5000 chars) |
| `voice` | string | `uz-UZ-MadinaNeural` | Voice ID, name, or language shortcut |
| `lang` | string | `uz` | Language code (uz, ru, en, tr, kk) |
| `gender` | string | — | `male` or `female` (used with `lang`) |
| `style` | string | `natural` | Voice style: natural, deep, chipmunk, hype, calm |
| `rate` | number | `0` | Speech rate adjustment |
| `pitch` | number | `0` | Pitch adjustment |
| `volume` | number | — | Volume adjustment |
| `dl` | string | — | Set to trigger download headers |
| `name` | string | — | Custom filename for download |

---

## 4. Downloading and Saving the MP3 File

> **Important distinction:**
> - **Generating** audio = sending text to the API and receiving MP3 bytes in the HTTP response
> - **Downloading** audio = writing those MP3 bytes to a file on disk
> - **Saving** audio = persisting the file for later use
>
> The API does not provide a permanent hosted URL for your audio.
> You receive the audio bytes directly in the response body.

### Python: Generate + Save in One Step

```python
import requests
from pathlib import Path

def generate_and_save(text, voice="sardor", output_path="output.mp3"):
    """Generate TTS audio and save it to a file."""
    response = requests.get(
        "https://tts-uzbek.onrender.com/tts.mp3",
        params={"q": text, "voice": voice},
        timeout=30
    )
    response.raise_for_status()

    # Verify we received audio data
    content_type = response.headers.get("Content-Type", "")
    if "audio" not in content_type:
        raise ValueError(f"Expected audio, got {content_type}")

    # Verify minimum file size (valid MP3 is at least a few hundred bytes)
    if len(response.content) < 256:
        raise ValueError("Audio data too small — likely an error")

    Path(output_path).write_bytes(response.content)
    return output_path

# Usage
saved_file = generate_and_save("Salom, bu sinov matni", voice="madina")
print(f"Saved to: {saved_file}")
```

### JavaScript (Node.js): Generate + Save in One Step

```javascript
import fs from "fs";

async function generateAndSave(text, voice = "sardor", outputPath = "output.mp3") {
    const params = new URLSearchParams({ q: text, voice });
    const response = await fetch(`https://tts-uzbek.onrender.com/tts.mp3?${params}`);

    if (!response.ok) {
        throw new Error(`TTS API error: ${response.status} ${response.statusText}`);
    }

    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("audio")) {
        throw new Error(`Expected audio, got ${contentType}`);
    }

    const buffer = Buffer.from(await response.arrayBuffer());

    if (buffer.length < 256) {
        throw new Error("Audio data too small — likely an error");
    }

    fs.writeFileSync(outputPath, buffer);
    return outputPath;
}

// Usage
const savedFile = await generateAndSave("Salom, bu sinov matni", "madina");
console.log(`Saved to: ${savedFile}`);
```

---

## 5. Returning Audio to Users

How an AI assistant delivers audio to the user depends on the platform and capabilities available.

### Scenario A: Generate a Direct Link

If the user can open a URL in their browser, provide them a direct link:

```
https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo&voice=sardor
```

The user can click this link to hear the audio or download it. This is the simplest approach and works on every platform.

### Scenario B: Save to Disk and Reference the File

If the AI assistant has file system access (e.g., in a coding environment):

```python
import requests

response = requests.get(
    "https://tts-uzbek.onrender.com/tts.mp3",
    params={"q": "Salom dunyo", "voice": "sardor"}
)

with open("speech.mp3", "wb") as f:
    f.write(response.content)

# Tell the user where the file is saved
print("Audio saved to: speech.mp3")
```

### Scenario C: Attach File to a Message

Some AI platforms support file attachments. If your platform supports it:

```python
# Platform-specific — this is pseudocode
audio_data = generate_audio("Salom dunyo")
send_message_with_attachment(user_id, audio_data, filename="speech.mp3", mime="audio/mpeg")
```

> **⚠️ Warning:** Most AI chat interfaces (ChatGPT, Claude, Gemini web, etc.)
> do **NOT** support attaching binary files to responses. In those contexts,
> provide the user with a direct URL link instead. Do not claim you have
> "generated and attached" an audio file if your platform does not support
> file attachments.

### Scenario D: Embed in HTML

If the AI is generating HTML content:

```html
<audio controls>
  <source src="https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo&voice=sardor" type="audio/mpeg">
  Your browser does not support audio playback.
</audio>
```

---

## 6. Error Handling

The API returns standard HTTP status codes. AI assistants should handle these gracefully.

### Error Response Codes

| Status Code | Meaning | What to Do |
|-------------|---------|------------|
| `400` | Bad Request — missing text, invalid voice, or invalid style | Check the `q`/`text` parameter is not empty; verify the voice name and style are valid |
| `413` | Payload Too Large — text exceeds 5000 characters | Split the text into smaller chunks (≤5000 chars each) and generate audio separately |
| `429` | Rate Limited — too many requests (>40/min per IP) | Wait for the duration indicated in the `Retry-After` header (typically 10 seconds), then retry |
| `502` | Bad Gateway — TTS engine error | Retry after a short delay (5–10 seconds). If persistent, the service may be temporarily unavailable |

### Python Error Handling Example

```python
import requests
import time

def generate_audio_safe(text, voice="sardor", max_retries=3):
    """Generate TTS audio with full error handling."""
    url = "https://tts-uzbek.onrender.com/tts.mp3"
    params = {"q": text, "voice": voice}

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "audio" in content_type and len(response.content) > 256:
                    return response.content
                else:
                    raise ValueError("Invalid audio response")

            elif response.status_code == 400:
                raise ValueError(f"Bad request: {response.text}")

            elif response.status_code == 413:
                raise ValueError(f"Text too long ({len(text)} chars). Maximum is 5000.")

            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                print(f"Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue

            elif response.status_code == 502:
                print(f"TTS engine error. Retrying in 5s... (attempt {attempt + 1})")
                time.sleep(5)
                continue

            else:
                raise RuntimeError(f"Unexpected status: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"Request timed out. Retrying... (attempt {attempt + 1})")
            time.sleep(3)
            continue

        except requests.exceptions.ConnectionError:
            print(f"Connection error. Retrying... (attempt {attempt + 1})")
            time.sleep(5)
            continue

    raise RuntimeError("Failed after maximum retries")
```

### JavaScript Error Handling Example

```javascript
async function generateAudioSafe(text, voice = "sardor", maxRetries = 3) {
    const url = "https://tts-uzbek.onrender.com/tts.mp3";

    for (let attempt = 0; attempt < maxRetries; attempt++) {
        const params = new URLSearchParams({ q: text, voice });
        const response = await fetch(`${url}?${params}`);

        if (response.ok) {
            const contentType = response.headers.get("content-type") || "";
            const buffer = Buffer.from(await response.arrayBuffer());

            if (contentType.includes("audio") && buffer.length > 256) {
                return buffer;
            }
            throw new Error("Invalid audio response");
        }

        if (response.status === 400) {
            throw new Error(`Bad request: ${await response.text()}`);
        }

        if (response.status === 413) {
            throw new Error(`Text too long (${text.length} chars). Maximum is 5000.`);
        }

        if (response.status === 429) {
            const retryAfter = parseInt(response.headers.get("retry-after") || "10", 10);
            console.log(`Rate limited. Waiting ${retryAfter}s...`);
            await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
            continue;
        }

        if (response.status === 502) {
            console.log(`TTS engine error. Retrying in 5s... (attempt ${attempt + 1})`);
            await new Promise(resolve => setTimeout(resolve, 5000));
            continue;
        }

        throw new Error(`Unexpected status: ${response.status}`);
    }

    throw new Error("Failed after maximum retries");
}
```

---

## 7. Verifying Audio Validity

After receiving a response, always verify that you received valid audio data.

### Verification Checklist

1. **HTTP status code is 200**
2. **Content-Type header contains `audio/mpeg`**
3. **Response body is at least 256 bytes** (very short audio is suspicious)
4. **MP3 magic bytes check** (optional): valid MP3 files start with `0xFF 0xFB`, `0xFF 0xF3`, `0xFF 0xF2`, or `0x49 0x44 0x33` (ID3 tag)

### Python Verification

```python
def verify_audio(response):
    """Verify that the HTTP response contains valid MP3 audio."""
    # Check status
    if response.status_code != 200:
        return False, f"HTTP {response.status_code}"

    # Check content type
    content_type = response.headers.get("Content-Type", "")
    if "audio" not in content_type:
        return False, f"Wrong content type: {content_type}"

    # Check minimum size
    data = response.content
    if len(data) < 256:
        return False, f"Too small: {len(data)} bytes"

    # Check MP3 magic bytes
    if data[:3] == b"ID3":
        return True, "Valid MP3 (ID3 header)"
    if data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return True, "Valid MP3 (sync header)"

    return False, "Unrecognized audio format"

# Usage
response = requests.get("https://tts-uzbek.onrender.com/tts.mp3?q=test")
is_valid, message = verify_audio(response)
print(f"Valid: {is_valid} — {message}")
```

### JavaScript Verification

```javascript
function verifyAudio(buffer, contentType) {
    if (!contentType || !contentType.includes("audio")) {
        return { valid: false, reason: `Wrong content type: ${contentType}` };
    }

    if (buffer.length < 256) {
        return { valid: false, reason: `Too small: ${buffer.length} bytes` };
    }

    // Check MP3 magic bytes
    if (buffer[0] === 0x49 && buffer[1] === 0x44 && buffer[2] === 0x33) {
        return { valid: true, reason: "Valid MP3 (ID3 header)" };
    }
    if (buffer[0] === 0xFF && (buffer[1] & 0xE0) === 0xE0) {
        return { valid: true, reason: "Valid MP3 (sync header)" };
    }

    return { valid: false, reason: "Unrecognized audio format" };
}
```

---

## 8. Complete Workflow Example

Here is a complete end-to-end workflow an AI assistant should follow:

### Python — Full Workflow

```python
import requests
import time
from pathlib import Path

BASE_URL = "https://tts-uzbek.onrender.com"

# Step 1: Check if service is available
health = requests.get(f"{BASE_URL}/health", timeout=5)
if health.status_code != 200:
    print("Service is unavailable. Try again later.")
    exit(1)

print("✅ Service is online")

# Step 2: List available voices
voices_response = requests.get(f"{BASE_URL}/api/voices", timeout=10)
voices_data = voices_response.json()
print(f"✅ Found {len(voices_data.get('voices', []))} voices")

# Step 3: Generate audio
text = "Assalomu alaykum! Uzbekcha TTS xizmatiga xush kelibsiz."
voice = "madina"

response = requests.get(
    f"{BASE_URL}/tts.mp3",
    params={"q": text, "voice": voice},
    timeout=30
)

# Step 4: Verify audio
if response.status_code != 200:
    print(f"❌ Error: HTTP {response.status_code}")
    exit(1)

content_type = response.headers.get("Content-Type", "")
if "audio" not in content_type:
    print(f"❌ Wrong content type: {content_type}")
    exit(1)

audio_data = response.content
if len(audio_data) < 256:
    print(f"❌ Audio too small: {len(audio_data)} bytes")
    exit(1)

print(f"✅ Received {len(audio_data)} bytes of audio")

# Step 5: Save to file
output_file = Path("uzbekcha_speech.mp3")
output_file.write_bytes(audio_data)
print(f"✅ Saved to: {output_file.absolute()}")

# Step 6: Provide to user
# Option A: Direct link (for chat interfaces)
from urllib.parse import urlencode
direct_url = f"{BASE_URL}/tts.mp3?{urlencode({'q': text, 'voice': voice})}"
print(f"🔗 Direct link: {direct_url}")

# Option B: Reference saved file (for coding environments)
print(f"📁 File saved at: {output_file.absolute()}")
```

### cURL — Full Workflow

```bash
# Step 1: Health check
curl -s -o /dev/null -w "%{http_code}" https://tts-uzbek.onrender.com/health

# Step 2: List voices
curl -s https://tts-uzbek.onrender.com/api/voices | python -m json.tool

# Step 3: Generate and save audio
curl -s -o speech.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo&voice=sardor"

# Step 4: Verify the file
file speech.mp3
# Expected output: speech.mp3: Audio file with ID3 version 2.4.0 ...

# Step 5: Check file size
ls -la speech.mp3
```

---

## 9. Important Limitations for AI Assistants

### What You CAN Do

- ✅ Generate a direct URL link for the user to click and listen
- ✅ Save MP3 files to disk (in coding/IDE environments)
- ✅ Generate audio programmatically via API calls
- ✅ Embed audio in HTML pages
- ✅ Process and verify audio data

### What You CANNOT Do (in Most Chat Interfaces)

- ❌ **Attach MP3 files to chat messages** — most AI chat platforms do not support binary file attachments in responses
- ❌ **Play audio directly** — AI text interfaces cannot play audio
- ❌ **Store audio permanently** — the service does not host generated audio at permanent URLs; each request regenerates (or serves from temporary cache)

### Best Practice for AI Assistants

When a user asks you to generate speech audio:

1. **Always provide the direct URL** so the user can listen immediately
2. **If you have file system access**, also save the file and tell the user the path
3. **Never claim you have "attached" audio** unless your platform genuinely supports it
4. **Handle errors gracefully** and explain what went wrong in plain language
5. **Respect rate limits** — do not generate more than 40 new requests per minute
6. **Split long texts** into chunks of ≤5000 characters if needed

---

## Quick Reference

| Action | Endpoint | Method |
|--------|----------|--------|
| Health check | `/health` | GET |
| Service info | `/api/info` | GET |
| List voices | `/api/voices` | GET |
| Generate audio (query) | `/tts.mp3?q=TEXT` | GET |
| Generate audio (JSON) | `/api/tts` | GET or POST |

**Base URL:** `https://tts-uzbek.onrender.com`

**Rate Limit:** 40 requests/minute per IP (cached responses don't count)

**Max Text Length:** 5000 characters per request
