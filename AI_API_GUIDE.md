# AI API Guide — Uzbekcha TTS

> **Complete API reference for AI agents, LLM tools, and automated integrations.**
>
> This document provides every endpoint, parameter, request/response example,
> and error handling detail an AI agent needs to interact with the Uzbekcha TTS service.

---

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [GET /api/info](#get-apiinfo)
  - [GET /api/voices](#get-apivoices)
  - [GET /tts.mp3](#get-ttsmp3)
  - [GET|POST /api/tts](#getpost-apitts)
  - [GET /](#get-)
- [Voice Selection Guide](#voice-selection-guide)
- [Styles Reference](#styles-reference)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Audio Verification](#audio-verification)
- [Best Practices for AI Agents](#best-practices-for-ai-agents)

---

## Base URL

```
https://tts-uzbek.onrender.com
```

Future URL (will also work):

```
https://uzbekcha-tts.onrender.com
```

---

## Authentication

**None required.** The API is completely public with no API keys, tokens, or authentication headers needed.

---

## Endpoints

### GET /health

Health check endpoint to verify the service is running.

**Aliases:** `/ping`

**Request:**

```
GET /health
```

**cURL:**

```bash
curl -i https://tts-uzbek.onrender.com/health
```

**Python:**

```python
import requests

response = requests.get("https://tts-uzbek.onrender.com/health", timeout=5)
print(response.status_code)  # 200 if healthy
print(response.text)
```

**JavaScript:**

```javascript
const response = await fetch("https://tts-uzbek.onrender.com/health");
console.log(response.status);  // 200 if healthy
console.log(await response.text());
```

**Response (200 OK):**

```
OK
```

---

### GET /api/info

Returns machine-readable service metadata designed for AI agent discovery.

**Request:**

```
GET /api/info
```

**cURL:**

```bash
curl -s https://tts-uzbek.onrender.com/api/info | python -m json.tool
```

**Python:**

```python
import requests

response = requests.get("https://tts-uzbek.onrender.com/api/info", timeout=10)
info = response.json()
print(f"Service: {info.get('name', 'unknown')}")
print(f"Description: {info.get('description', '')}")
```

**JavaScript:**

```javascript
const response = await fetch("https://tts-uzbek.onrender.com/api/info");
const info = await response.json();
console.log(`Service: ${info.name}`);
console.log(`Description: ${info.description}`);
```

**Response (200 OK):**

```json
{
  "name": "Uzbekcha TTS",
  "description": "Free text-to-speech API supporting Uzbek, Russian, English, Turkish, and Kazakh",
  "version": "2.0.0",
  "endpoints": {
    "tts": "/tts.mp3?q=TEXT",
    "api_tts": "/api/tts",
    "voices": "/api/voices",
    "health": "/health"
  },
  "limits": {
    "max_text_length": 5000,
    "rate_limit": "40 req/min per IP"
  },
  "default_voice": "uz-UZ-MadinaNeural",
  "supported_languages": ["uz", "ru", "en", "tr", "kk"]
}
```

---

### GET /api/voices

Returns the full list of available voices, styles, and service metadata.

**Request:**

```
GET /api/voices
```

**cURL:**

```bash
curl -s https://tts-uzbek.onrender.com/api/voices | python -m json.tool
```

**Python:**

```python
import requests

response = requests.get("https://tts-uzbek.onrender.com/api/voices", timeout=10)
data = response.json()

# List all voices
for voice in data.get("voices", []):
    print(f"  {voice['id']} — {voice['name']} ({voice['locale']}, {voice['gender']})")

# List available styles
print(f"Styles: {data.get('styles', [])}")
```

**JavaScript:**

```javascript
const response = await fetch("https://tts-uzbek.onrender.com/api/voices");
const data = await response.json();

data.voices.forEach(voice => {
    console.log(`  ${voice.id} — ${voice.name} (${voice.locale}, ${voice.gender})`);
});

console.log(`Styles: ${data.styles.join(", ")}`);
```

**Response (200 OK):**

```json
{
  "voices": [
    {
      "id": "uz-UZ-SardorNeural",
      "name": "Sardor",
      "locale": "uz-UZ",
      "language": "uz",
      "gender": "male"
    },
    {
      "id": "uz-UZ-MadinaNeural",
      "name": "Madina",
      "locale": "uz-UZ",
      "language": "uz",
      "gender": "female"
    },
    {
      "id": "ru-RU-DmitryNeural",
      "name": "Dmitry",
      "locale": "ru-RU",
      "language": "ru",
      "gender": "male"
    },
    {
      "id": "ru-RU-SvetlanaNeural",
      "name": "Svetlana",
      "locale": "ru-RU",
      "language": "ru",
      "gender": "female"
    },
    {
      "id": "en-US-AndrewNeural",
      "name": "Andrew",
      "locale": "en-US",
      "language": "en",
      "gender": "male"
    },
    {
      "id": "en-US-AriaNeural",
      "name": "Aria",
      "locale": "en-US",
      "language": "en",
      "gender": "female"
    },
    {
      "id": "tr-TR-AhmetNeural",
      "name": "Ahmet",
      "locale": "tr-TR",
      "language": "tr",
      "gender": "male"
    },
    {
      "id": "tr-TR-EmelNeural",
      "name": "Emel",
      "locale": "tr-TR",
      "language": "tr",
      "gender": "female"
    },
    {
      "id": "kk-KZ-DauletNeural",
      "name": "Daulet",
      "locale": "kk-KZ",
      "language": "kk",
      "gender": "male"
    },
    {
      "id": "kk-KZ-AigulNeural",
      "name": "Aigul",
      "locale": "kk-KZ",
      "language": "kk",
      "gender": "female"
    }
  ],
  "styles": ["natural", "deep", "chipmunk", "hype", "calm"],
  "limits": {
    "max_text_length": 5000,
    "rate_limit_per_minute": 40
  }
}
```

---

### GET /tts.mp3

Generate speech audio from text. Returns binary MP3 audio data.

**Request:**

```
GET /tts.mp3?q=TEXT&voice=VOICE&style=STYLE&rate=RATE&pitch=PITCH
```

**Parameters (all via query string):**

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `q` | **Yes** | string | — | Text to synthesize (max 5000 characters) |
| `voice` | No | string | `uz-UZ-MadinaNeural` | Voice identifier (full ID, short name, or language shortcut) |
| `lang` | No | string | `uz` | Language code: `uz`, `ru`, `en`, `tr`, `kk` |
| `gender` | No | string | — | `male` or `female` (used with `lang`) |
| `style` | No | string | `natural` | Style: `natural`, `deep`, `chipmunk`, `hype`, `calm` |
| `rate` | No | number | `0` | Speech rate adjustment |
| `pitch` | No | number | `0` | Pitch adjustment |
| `volume` | No | number | — | Volume adjustment |
| `dl` | No | string | — | Triggers `Content-Disposition: attachment` header |
| `name` | No | string | — | Custom filename for downloads |
| `sig` | No | string | — | Signature for pre-signed URLs |

**Response:**

- **Content-Type:** `audio/mpeg`
- **Body:** Binary MP3 audio data

**cURL:**

```bash
# Basic usage — save to file
curl -o speech.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo"

# With voice and style
curl -o speech.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo&voice=sardor&style=deep"

# With language + gender selection
curl -o speech.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Hello%20world&lang=en&gender=female"
```

**Python:**

```python
import requests

# Basic usage
response = requests.get(
    "https://tts-uzbek.onrender.com/tts.mp3",
    params={"q": "Salom dunyo", "voice": "sardor"},
    timeout=30
)

if response.status_code == 200:
    with open("speech.mp3", "wb") as f:
        f.write(response.content)
    print(f"Saved {len(response.content)} bytes")

# With all parameters
response = requests.get(
    "https://tts-uzbek.onrender.com/tts.mp3",
    params={
        "q": "Salom dunyo",
        "voice": "uz-UZ-SardorNeural",
        "style": "deep",
        "rate": 0,
        "pitch": 0
    },
    timeout=30
)
```

**JavaScript:**

```javascript
// Basic usage
const params = new URLSearchParams({
    q: "Salom dunyo",
    voice: "sardor"
});

const response = await fetch(`https://tts-uzbek.onrender.com/tts.mp3?${params}`);

if (response.ok) {
    const buffer = Buffer.from(await response.arrayBuffer());
    const fs = await import("fs");
    fs.writeFileSync("speech.mp3", buffer);
    console.log(`Saved ${buffer.length} bytes`);
}
```

---

### GET|POST /api/tts

Alternative TTS endpoint that also accepts JSON request bodies. Returns binary MP3 audio.

**GET Request (same as /tts.mp3):**

```
GET /api/tts?q=TEXT&voice=VOICE&style=STYLE
```

**POST Request (JSON body):**

```
POST /api/tts
Content-Type: application/json

{
  "text": "Salom dunyo",
  "voice": "sardor",
  "style": "natural",
  "rate": 0,
  "pitch": 0
}
```

**JSON Body Parameters:**

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `text` | **Yes** | string | — | Text to synthesize (max 5000 characters) |
| `voice` | No | string | `uz-UZ-MadinaNeural` | Voice identifier |
| `style` | No | string | `natural` | Voice style |
| `rate` | No | number | `0` | Speech rate adjustment |
| `pitch` | No | number | `0` | Pitch adjustment |

**Response:**

- **Content-Type:** `audio/mpeg`
- **Body:** Binary MP3 audio data

**cURL (POST with JSON):**

```bash
curl -X POST "https://tts-uzbek.onrender.com/api/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Salom dunyo", "voice": "sardor", "style": "natural"}' \
  -o speech.mp3
```

**Python (POST with JSON):**

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
    },
    timeout=30
)

if response.status_code == 200:
    with open("speech.mp3", "wb") as f:
        f.write(response.content)
    print(f"Generated {len(response.content)} bytes of audio")
else:
    print(f"Error: {response.status_code} — {response.text}")
```

**JavaScript (POST with JSON):**

```javascript
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
    console.log(`Generated ${buffer.length} bytes of audio`);
    // Save or process the buffer
}
```

---

### GET /

The root endpoint serves the web interface by default. However, if `?q=` or `?r=` query parameters are present, it returns MP3 audio directly (same behavior as `/tts.mp3`).

**As a web page:**

```
GET /
```

Returns: HTML web interface.

**As an audio endpoint:**

```
GET /?q=Salom%20dunyo&voice=sardor
```

Returns: `audio/mpeg` binary MP3 data.

> **For AI agents:** Prefer `/tts.mp3` or `/api/tts` instead of using `/` for audio generation. The explicit endpoints are clearer and will not change behavior.

---

## Voice Selection Guide

The API provides multiple convenient ways to select a voice:

### By Full Voice ID

The most explicit method. Use the complete voice identifier:

```
voice=uz-UZ-SardorNeural
voice=en-US-AriaNeural
voice=ru-RU-DmitryNeural
```

### By Short Name

Case-insensitive short name matching:

```
voice=sardor
voice=madina
voice=dmitry
voice=aria
voice=ahmet
```

### By Language Code

Uses the default voice for that language:

```
lang=uz    → uz-UZ-MadinaNeural (female, default)
lang=ru    → ru-RU-SvetlanaNeural (female, default)
lang=en    → en-US-AriaNeural (female, default)
lang=tr    → tr-TR-EmelNeural (female, default)
lang=kk    → kk-KZ-AigulNeural (female, default)
```

### By Language + Gender (Combined)

Use the `voice` parameter with a combined string:

```
voice=uz-female   → uz-UZ-MadinaNeural
voice=uz-male     → uz-UZ-SardorNeural
voice=ru-male     → ru-RU-DmitryNeural
voice=en-female   → en-US-AriaNeural
```

### By Separate Language and Gender Parameters

```
lang=uz&gender=male     → uz-UZ-SardorNeural
lang=en&gender=female   → en-US-AriaNeural
lang=ru&gender=female   → ru-RU-SvetlanaNeural
```

### Complete Voice Reference Table

| Voice ID | Short Name | Language | Gender |
|----------|-----------|----------|--------|
| `uz-UZ-SardorNeural` | sardor | uz | male |
| `uz-UZ-MadinaNeural` | madina | uz | female |
| `ru-RU-DmitryNeural` | dmitry | ru | male |
| `ru-RU-SvetlanaNeural` | svetlana | ru | female |
| `en-US-AndrewNeural` | andrew | en | male |
| `en-US-AriaNeural` | aria | en | female |
| `tr-TR-AhmetNeural` | ahmet | tr | male |
| `tr-TR-EmelNeural` | emel | tr | female |
| `kk-KZ-DauletNeural` | daulet | kk | male |
| `kk-KZ-AigulNeural` | aigul | kk | female |

---

## Styles Reference

The `style` parameter changes how the voice sounds:

| Style | Description |
|-------|-------------|
| `natural` | Standard, natural-sounding speech (default) |
| `deep` | Lower, deeper voice tone |
| `chipmunk` | Higher-pitched, faster voice |
| `hype` | Energetic, enthusiastic delivery |
| `calm` | Slower, more relaxed and soothing delivery |

**Example:**

```bash
# Deep voice
curl -o deep.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom&voice=sardor&style=deep"

# Calm voice
curl -o calm.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom&voice=madina&style=calm"
```

---

## Error Handling

### Error Response Format

Error responses return plain text or JSON bodies with an appropriate HTTP status code.

### Error Codes

| Status | Meaning | Cause | AI Agent Action |
|--------|---------|-------|-----------------|
| `400` | Bad Request | Missing `q`/`text` parameter, invalid voice ID, invalid style name | Fix the request parameters and retry |
| `413` | Payload Too Large | Text exceeds 5000 characters | Split text into chunks of ≤5000 characters |
| `429` | Too Many Requests | More than 40 new-text requests per minute from same IP | Read `Retry-After` header (default: 10s), wait, then retry |
| `502` | Bad Gateway | Upstream TTS engine failure | Wait 5–10 seconds and retry; if persistent, service is temporarily down |

### Error Handling Example (Python)

```python
import requests
import time

def call_tts_api(text, voice="sardor", max_retries=3):
    url = "https://tts-uzbek.onrender.com/tts.mp3"

    for attempt in range(max_retries):
        response = requests.get(url, params={"q": text, "voice": voice}, timeout=30)

        if response.status_code == 200:
            return response.content

        if response.status_code == 400:
            raise ValueError(f"Bad request: {response.text}")

        if response.status_code == 413:
            raise ValueError(f"Text too long ({len(text)} chars). Max: 5000")

        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 10))
            time.sleep(wait)
            continue

        if response.status_code == 502:
            time.sleep(5)
            continue

        raise RuntimeError(f"Unexpected error: {response.status_code}")

    raise RuntimeError("Max retries exceeded")
```

### Error Handling Example (JavaScript)

```javascript
async function callTtsApi(text, voice = "sardor", maxRetries = 3) {
    const url = "https://tts-uzbek.onrender.com/tts.mp3";

    for (let i = 0; i < maxRetries; i++) {
        const params = new URLSearchParams({ q: text, voice });
        const response = await fetch(`${url}?${params}`);

        if (response.ok) {
            return Buffer.from(await response.arrayBuffer());
        }

        if (response.status === 400) {
            throw new Error(`Bad request: ${await response.text()}`);
        }

        if (response.status === 413) {
            throw new Error(`Text too long (${text.length} chars). Max: 5000`);
        }

        if (response.status === 429) {
            const wait = parseInt(response.headers.get("retry-after") || "10", 10);
            await new Promise(r => setTimeout(r, wait * 1000));
            continue;
        }

        if (response.status === 502) {
            await new Promise(r => setTimeout(r, 5000));
            continue;
        }

        throw new Error(`Unexpected error: ${response.status}`);
    }

    throw new Error("Max retries exceeded");
}
```

---

## Rate Limiting

| Property | Value |
|----------|-------|
| **Limit** | 40 requests per minute per IP address |
| **Applies to** | New text only — requests served from cache do not count |
| **Response when exceeded** | HTTP `429 Too Many Requests` |
| **Retry-After header** | Present with value `10` (seconds) |
| **Reset** | Rolling window — no fixed reset time |

### How to Handle Rate Limiting

1. Check the response status code for `429`
2. Read the `Retry-After` header value
3. Wait that many seconds before retrying
4. Implement exponential backoff for sustained rate limiting

### Optimizing for Cache Hits

- Identical text + voice + style combinations are served from cache and do not count against the rate limit
- If you need to generate audio for the same text multiple times, the second and subsequent requests will be instant and free

---

## Audio Verification

After receiving a response, AI agents should verify the audio data before using it.

### Step-by-Step Verification

```python
def verify_tts_response(response):
    """
    Verify a TTS API response contains valid MP3 audio.
    Returns (is_valid, audio_bytes_or_none, error_message).
    """
    # 1. Check HTTP status
    if response.status_code != 200:
        return False, None, f"HTTP {response.status_code}: {response.text}"

    # 2. Check Content-Type
    content_type = response.headers.get("Content-Type", "")
    if "audio" not in content_type:
        return False, None, f"Expected audio/mpeg, got: {content_type}"

    # 3. Check body size
    data = response.content
    if len(data) < 256:
        return False, None, f"Response too small ({len(data)} bytes)"

    # 4. Check MP3 magic bytes
    has_id3 = data[:3] == b"ID3"
    has_sync = data[0] == 0xFF and (data[1] & 0xE0) == 0xE0
    if not has_id3 and not has_sync:
        return False, None, "Missing MP3 header bytes"

    # 5. All checks passed
    return True, data, f"Valid MP3, {len(data)} bytes"
```

### Quick Verification Checklist

| Check | Expected Value | Failure Meaning |
|-------|---------------|-----------------|
| `response.status_code` | `200` | Request failed — check error code |
| `Content-Type` header | Contains `audio` | Response is not audio data |
| `len(response.content)` | `≥ 256` | Response is too small to be valid audio |
| First 3 bytes | `ID3` or `0xFF 0xFx` | Not a valid MP3 file |

---

## Best Practices for AI Agents

1. **Always check service health first** — call `/health` before making TTS requests
2. **Use `/api/tts` with POST** for the cleanest integration — it accepts JSON and is the most explicit endpoint
3. **Cache voice information** — call `/api/voices` once and reuse the results
4. **Validate text length** before sending — check that `len(text) <= 5000`
5. **Verify audio responses** — check Content-Type and file size before saving
6. **Handle errors gracefully** — implement retry logic for 429 and 502 errors
7. **Provide direct URLs to users** when possible — don't claim to "attach" files in platforms that don't support it
8. **Use short voice names** for simplicity — `sardor` is easier than `uz-UZ-SardorNeural`
9. **Prefer the `natural` style** unless the user specifically requests a different one
10. **Split long texts** into ≤5000 character chunks and generate audio for each chunk separately
