# API Documentation — Uzbekcha TTS

> **Free, open text-to-speech API supporting Uzbek, Russian, English, Turkish, and Kazakh.**
>
> No authentication required. No account needed. Just send text, get audio.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Quick Start](#quick-start)
- [Endpoints Reference](#endpoints-reference)
  - [Health Check](#health-check)
  - [Generate Audio — GET /tts.mp3](#generate-audio--get-ttsmp3)
  - [Generate Audio — POST /api/tts](#generate-audio--post-apitts)
  - [List Voices — GET /api/voices](#list-voices--get-apivoices)
  - [Service Info — GET /api/info](#service-info--get-apiinfo)
- [Voice Selection Guide](#voice-selection-guide)
- [Styles](#styles)
- [Code Examples](#code-examples)
  - [Python](#python)
  - [JavaScript / Node.js](#javascript--nodejs)
  - [cURL](#curl)
  - [PowerShell](#powershell)
- [Rate Limiting](#rate-limiting)
- [Error Codes](#error-codes)
- [Integration Patterns](#integration-patterns)

---

## Overview

Uzbekcha TTS is a free text-to-speech service powered by Microsoft Edge Neural TTS technology. It converts text into natural-sounding speech audio (MP3 format) across five languages with ten distinct neural voices.

### Key Features

- **5 languages:** Uzbek, Russian, English, Turkish, Kazakh
- **10 neural voices:** Male and female for each language
- **5 voice styles:** natural, deep, chipmunk, hype, calm
- **No authentication:** Completely free and open
- **Fast response:** Cached results are served instantly
- **Standard MP3 output:** Compatible with any audio player

---

## Authentication

**No authentication is required.** There are no API keys, tokens, OAuth flows, or account registrations needed. The API is open and available to everyone.

---

## Base URL

```
https://tts-uzbek.onrender.com
```

All endpoint paths in this document are relative to this base URL.

---

## Quick Start

Generate your first audio in one command:

```bash
curl -o hello.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo"
```

That's it. Open `hello.mp3` to hear "Salom dunyo" spoken in Uzbek.

---

## Endpoints Reference

### Health Check

Verify the service is running and ready to accept requests.

| Property | Value |
|----------|-------|
| **Endpoint** | `GET /health` or `GET /ping` |
| **Response** | `200 OK` with body `OK` |

```bash
curl https://tts-uzbek.onrender.com/health
```

---

### Generate Audio — GET /tts.mp3

Convert text to speech and receive MP3 audio.

| Property | Value |
|----------|-------|
| **Method** | `GET` |
| **Endpoint** | `/tts.mp3` |
| **Response Type** | `audio/mpeg` (binary MP3) |

#### Query Parameters

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `q` | **Yes** | string | — | Text to convert to speech (max 5000 chars) |
| `voice` | No | string | `uz-UZ-MadinaNeural` | Voice selection (see [Voice Selection Guide](#voice-selection-guide)) |
| `lang` | No | string | `uz` | Language code: `uz`, `ru`, `en`, `tr`, `kk` |
| `gender` | No | string | — | Gender: `male` or `female` (used with `lang`) |
| `style` | No | string | `natural` | Voice style (see [Styles](#styles)) |
| `rate` | No | number | `0` | Speech rate adjustment |
| `pitch` | No | number | `0` | Voice pitch adjustment |
| `volume` | No | number | — | Volume adjustment |
| `dl` | No | string | — | If set, adds `Content-Disposition: attachment` header |
| `name` | No | string | — | Custom filename for download |
| `sig` | No | string | — | Signature for pre-signed URLs |

#### Examples

```bash
# Default Uzbek female voice
curl -o output.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom"

# Specific voice by name
curl -o output.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Hello&voice=aria"

# Language + gender selection
curl -o output.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Привет&lang=ru&gender=male"

# With style
curl -o output.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom&voice=sardor&style=deep"
```

---

### Generate Audio — POST /api/tts

Alternative endpoint that accepts JSON request bodies. Also supports GET with query parameters (same as `/tts.mp3`).

| Property | Value |
|----------|-------|
| **Method** | `GET` or `POST` |
| **Endpoint** | `/api/tts` |
| **Request Body (POST)** | `application/json` |
| **Response Type** | `audio/mpeg` (binary MP3) |

#### JSON Body Parameters (POST)

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `text` | **Yes** | string | — | Text to convert to speech (max 5000 chars) |
| `voice` | No | string | `uz-UZ-MadinaNeural` | Voice selection |
| `style` | No | string | `natural` | Voice style |
| `rate` | No | number | `0` | Speech rate adjustment |
| `pitch` | No | number | `0` | Pitch adjustment |

#### Example

```bash
curl -X POST "https://tts-uzbek.onrender.com/api/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Salom dunyo", "voice": "sardor"}' \
  -o output.mp3
```

---

### List Voices — GET /api/voices

Get the complete list of available voices, styles, and service limits.

| Property | Value |
|----------|-------|
| **Method** | `GET` |
| **Endpoint** | `/api/voices` |
| **Response Type** | `application/json` |

#### Response Structure

```json
{
  "voices": [
    {
      "id": "uz-UZ-SardorNeural",
      "name": "Sardor",
      "locale": "uz-UZ",
      "language": "uz",
      "gender": "male"
    }
  ],
  "styles": ["natural", "deep", "chipmunk", "hype", "calm"],
  "limits": {
    "max_text_length": 5000,
    "rate_limit_per_minute": 40
  }
}
```

#### Example

```bash
curl -s https://tts-uzbek.onrender.com/api/voices | python -m json.tool
```

---

### Service Info — GET /api/info

Machine-readable service metadata for automated integrations and AI agent discovery.

| Property | Value |
|----------|-------|
| **Method** | `GET` |
| **Endpoint** | `/api/info` |
| **Response Type** | `application/json` |

#### Example

```bash
curl -s https://tts-uzbek.onrender.com/api/info | python -m json.tool
```

---

## Voice Selection Guide

The API offers flexible voice selection with multiple methods:

### Available Voices

| Language | Code | Male Voice | Female Voice |
|----------|------|-----------|--------------|
| Uzbek | `uz` | `uz-UZ-SardorNeural` (Sardor) | `uz-UZ-MadinaNeural` (Madina) |
| Russian | `ru` | `ru-RU-DmitryNeural` (Dmitry) | `ru-RU-SvetlanaNeural` (Svetlana) |
| English | `en` | `en-US-AndrewNeural` (Andrew) | `en-US-AriaNeural` (Aria) |
| Turkish | `tr` | `tr-TR-AhmetNeural` (Ahmet) | `tr-TR-EmelNeural` (Emel) |
| Kazakh | `kk` | `kk-KZ-DauletNeural` (Daulet) | `kk-KZ-AigulNeural` (Aigul) |

### Selection Methods

#### 1. By Full Voice ID (Most Explicit)

```
voice=uz-UZ-SardorNeural
voice=en-US-AriaNeural
```

#### 2. By Short Name (Easiest)

```
voice=sardor
voice=aria
voice=dmitry
```

Short names are case-insensitive.

#### 3. By Language Code

```
lang=uz      →  defaults to uz-UZ-MadinaNeural
lang=en      →  defaults to en-US-AriaNeural
```

#### 4. By Language + Gender (Combined)

```
voice=uz-male      →  uz-UZ-SardorNeural
voice=uz-female    →  uz-UZ-MadinaNeural
voice=en-female    →  en-US-AriaNeural
```

#### 5. By Separate Parameters

```
lang=uz&gender=female    →  uz-UZ-MadinaNeural
lang=ru&gender=male      →  ru-RU-DmitryNeural
```

---

## Styles

Styles change the tone and delivery of the voice:

| Style | Effect |
|-------|--------|
| `natural` | Standard natural-sounding speech **(default)** |
| `deep` | Lower, deeper voice tone |
| `chipmunk` | Higher-pitched, faster delivery |
| `hype` | Energetic, enthusiastic delivery |
| `calm` | Slower, more relaxed, soothing delivery |

**Usage:**

```bash
curl -o deep.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom&style=deep"
curl -o calm.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom&style=calm"
```

---

## Code Examples

### Python

#### Basic Usage

```python
import requests

response = requests.get(
    "https://tts-uzbek.onrender.com/tts.mp3",
    params={"q": "Salom dunyo!", "voice": "sardor"},
    timeout=30
)

if response.status_code == 200:
    with open("output.mp3", "wb") as f:
        f.write(response.content)
    print(f"Audio saved: {len(response.content)} bytes")
else:
    print(f"Error: {response.status_code}")
```

#### Using POST with JSON

```python
import requests

response = requests.post(
    "https://tts-uzbek.onrender.com/api/tts",
    json={
        "text": "Assalomu alaykum!",
        "voice": "madina",
        "style": "natural"
    },
    timeout=30
)

if response.status_code == 200:
    with open("output.mp3", "wb") as f:
        f.write(response.content)
```

#### Listing Voices

```python
import requests

response = requests.get("https://tts-uzbek.onrender.com/api/voices")
data = response.json()

for voice in data["voices"]:
    print(f"{voice['id']:30s} {voice['name']:12s} {voice['locale']:8s} {voice['gender']}")
```

#### Production-Ready Function with Error Handling

```python
import requests
import time
from pathlib import Path

def text_to_speech(
    text: str,
    voice: str = "madina",
    style: str = "natural",
    output: str = "output.mp3",
    max_retries: int = 3
) -> str:
    """
    Convert text to speech and save as MP3.

    Args:
        text: Text to synthesize (max 5000 characters).
        voice: Voice name or ID.
        style: Voice style (natural, deep, chipmunk, hype, calm).
        output: Output file path.
        max_retries: Maximum number of retry attempts.

    Returns:
        Path to the saved audio file.

    Raises:
        ValueError: If the request is invalid.
        RuntimeError: If the request fails after retries.
    """
    if len(text) > 5000:
        raise ValueError(f"Text too long: {len(text)} chars (max 5000)")

    url = "https://tts-uzbek.onrender.com/tts.mp3"
    params = {"q": text, "voice": voice, "style": style}

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "audio" not in content_type:
                    raise RuntimeError(f"Unexpected content type: {content_type}")
                if len(response.content) < 256:
                    raise RuntimeError("Audio response too small")

                Path(output).write_bytes(response.content)
                return output

            elif response.status_code == 400:
                raise ValueError(f"Invalid request: {response.text}")

            elif response.status_code == 413:
                raise ValueError("Text exceeds 5000 character limit")

            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                time.sleep(retry_after)
                continue

            elif response.status_code == 502:
                time.sleep(5)
                continue

            else:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            raise RuntimeError(f"Connection failed: {e}")

    raise RuntimeError("Failed after maximum retries")


# Usage:
saved = text_to_speech("Salom dunyo!", voice="sardor", style="deep")
print(f"Saved to: {saved}")
```

---

### JavaScript / Node.js

#### Basic Usage (ES Modules)

```javascript
import fs from "fs";

const params = new URLSearchParams({
    q: "Hello world!",
    voice: "aria"
});

const response = await fetch(`https://tts-uzbek.onrender.com/tts.mp3?${params}`);

if (response.ok) {
    const buffer = Buffer.from(await response.arrayBuffer());
    fs.writeFileSync("output.mp3", buffer);
    console.log(`Audio saved: ${buffer.length} bytes`);
} else {
    console.error(`Error: ${response.status}`);
}
```

#### Using POST with JSON

```javascript
const response = await fetch("https://tts-uzbek.onrender.com/api/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        text: "Assalomu alaykum!",
        voice: "madina",
        style: "natural"
    })
});

if (response.ok) {
    const buffer = Buffer.from(await response.arrayBuffer());
    const fs = await import("fs");
    fs.writeFileSync("output.mp3", buffer);
}
```

#### Listing Voices

```javascript
const response = await fetch("https://tts-uzbek.onrender.com/api/voices");
const data = await response.json();

data.voices.forEach(voice => {
    console.log(`${voice.id.padEnd(30)} ${voice.name.padEnd(12)} ${voice.locale.padEnd(8)} ${voice.gender}`);
});
```

#### Production-Ready Function

```javascript
import fs from "fs";

/**
 * Convert text to speech and save as MP3.
 * @param {string} text - Text to synthesize (max 5000 characters).
 * @param {object} options - Configuration options.
 * @param {string} options.voice - Voice name or ID (default: "madina").
 * @param {string} options.style - Voice style (default: "natural").
 * @param {string} options.output - Output file path (default: "output.mp3").
 * @param {number} options.maxRetries - Maximum retries (default: 3).
 * @returns {Promise<string>} Path to the saved audio file.
 */
async function textToSpeech(text, { voice = "madina", style = "natural", output = "output.mp3", maxRetries = 3 } = {}) {
    if (text.length > 5000) {
        throw new Error(`Text too long: ${text.length} chars (max 5000)`);
    }

    const url = "https://tts-uzbek.onrender.com/tts.mp3";

    for (let attempt = 0; attempt < maxRetries; attempt++) {
        const params = new URLSearchParams({ q: text, voice, style });
        const response = await fetch(`${url}?${params}`);

        if (response.ok) {
            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes("audio")) {
                throw new Error(`Unexpected content type: ${contentType}`);
            }

            const buffer = Buffer.from(await response.arrayBuffer());
            if (buffer.length < 256) {
                throw new Error("Audio response too small");
            }

            fs.writeFileSync(output, buffer);
            return output;
        }

        if (response.status === 400) {
            throw new Error(`Invalid request: ${await response.text()}`);
        }

        if (response.status === 413) {
            throw new Error("Text exceeds 5000 character limit");
        }

        if (response.status === 429) {
            const retryAfter = parseInt(response.headers.get("retry-after") || "10", 10);
            await new Promise(r => setTimeout(r, retryAfter * 1000));
            continue;
        }

        if (response.status === 502) {
            await new Promise(r => setTimeout(r, 5000));
            continue;
        }

        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    throw new Error("Failed after maximum retries");
}

// Usage:
const saved = await textToSpeech("Salom dunyo!", { voice: "sardor", style: "deep" });
console.log(`Saved to: ${saved}`);
```

---

### cURL

```bash
# Basic — default Uzbek voice
curl -o output.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo"

# Specific voice
curl -o output.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Hello%20world&voice=aria"

# Voice by language + gender
curl -o output.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Привет%20мир&lang=ru&gender=male"

# With style
curl -o output.mp3 "https://tts-uzbek.onrender.com/tts.mp3?q=Salom&voice=sardor&style=deep"

# POST with JSON
curl -X POST "https://tts-uzbek.onrender.com/api/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Salom dunyo", "voice": "sardor", "style": "natural"}' \
  -o output.mp3

# List voices
curl -s https://tts-uzbek.onrender.com/api/voices | python -m json.tool

# Health check
curl -i https://tts-uzbek.onrender.com/health
```

---

### PowerShell

#### Basic Usage

```powershell
# Generate audio
Invoke-WebRequest -Uri "https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo&voice=sardor" -OutFile "output.mp3"

# Check file
Get-Item "output.mp3" | Select-Object Name, Length
```

#### Using POST with JSON

```powershell
$body = @{
    text  = "Assalomu alaykum!"
    voice = "madina"
    style = "natural"
} | ConvertTo-Json

Invoke-WebRequest `
    -Uri "https://tts-uzbek.onrender.com/api/tts" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body `
    -OutFile "output.mp3"
```

#### Listing Voices

```powershell
$voices = Invoke-RestMethod -Uri "https://tts-uzbek.onrender.com/api/voices"
$voices.voices | Format-Table id, name, locale, gender
```

#### Production-Ready Function

```powershell
function ConvertTo-Speech {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateLength(1, 5000)]
        [string]$Text,

        [string]$Voice = "madina",
        [ValidateSet("natural", "deep", "chipmunk", "hype", "calm")]
        [string]$Style = "natural",
        [string]$OutputPath = "output.mp3",
        [int]$MaxRetries = 3
    )

    $baseUrl = "https://tts-uzbek.onrender.com/tts.mp3"
    $encodedText = [System.Uri]::EscapeDataString($Text)
    $url = "${baseUrl}?q=${encodedText}&voice=${Voice}&style=${Style}"

    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $url -OutFile $OutputPath -PassThru -ErrorAction Stop

            if ($response.StatusCode -eq 200) {
                $fileInfo = Get-Item $OutputPath
                if ($fileInfo.Length -lt 256) {
                    throw "Audio file too small: $($fileInfo.Length) bytes"
                }
                Write-Output "Audio saved to: $OutputPath ($($fileInfo.Length) bytes)"
                return $OutputPath
            }
        }
        catch {
            $statusCode = $_.Exception.Response.StatusCode.value__

            if ($statusCode -eq 429) {
                Write-Warning "Rate limited. Waiting 10 seconds..."
                Start-Sleep -Seconds 10
                continue
            }
            elseif ($statusCode -eq 502) {
                Write-Warning "TTS engine error. Retrying in 5 seconds..."
                Start-Sleep -Seconds 5
                continue
            }
            else {
                throw $_
            }
        }
    }

    throw "Failed after $MaxRetries attempts"
}

# Usage:
ConvertTo-Speech -Text "Salom dunyo!" -Voice "sardor" -Style "deep" -OutputPath "speech.mp3"
```

---

## Rate Limiting

| Property | Value |
|----------|-------|
| **Rate Limit** | 40 requests per minute per IP address |
| **Applies To** | New text generations only |
| **Cached Requests** | Do not count against the limit |
| **Exceeded Response** | `429 Too Many Requests` |
| **Retry-After Header** | `10` (seconds) |

### Tips

- Identical text + voice + style combinations are served from cache and are free
- Space out requests when processing large batches
- Implement retry logic with the `Retry-After` header value

---

## Error Codes

| Code | Status | Description | Resolution |
|------|--------|-------------|------------|
| `400` | Bad Request | Missing text, invalid voice, or invalid style | Check required parameters and valid values |
| `413` | Payload Too Large | Text exceeds 5000 characters | Split text into smaller chunks |
| `429` | Too Many Requests | Rate limit exceeded (40 req/min) | Wait for `Retry-After` seconds and retry |
| `502` | Bad Gateway | TTS engine failure | Retry after 5–10 seconds |

### Error Response Example

```
HTTP/1.1 429 Too Many Requests
Retry-After: 10
Content-Type: text/plain

Rate limit exceeded. Please wait before making more requests.
```

---

## Integration Patterns

### Pattern 1: Simple One-Shot Generation

Best for: single audio files, simple scripts.

```python
import requests

audio = requests.get("https://tts-uzbek.onrender.com/tts.mp3?q=Salom").content
open("output.mp3", "wb").write(audio)
```

### Pattern 2: Batch Processing

Best for: converting multiple texts, audiobook chapters, content pipelines.

```python
import requests
import time

texts = [
    ("chapter1.mp3", "Birinchi bob. Hikoya boshlanadi..."),
    ("chapter2.mp3", "Ikkinchi bob. Voqealar davom etadi..."),
    ("chapter3.mp3", "Uchinchi bob. Yakuniy qism..."),
]

for filename, text in texts:
    response = requests.get(
        "https://tts-uzbek.onrender.com/tts.mp3",
        params={"q": text, "voice": "sardor"},
        timeout=30
    )

    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ {filename}")
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))
        time.sleep(retry_after)
    else:
        print(f"❌ {filename}: HTTP {response.status_code}")

    time.sleep(1.5)  # Be respectful of rate limits
```

### Pattern 3: HTML/Web Embedding

Best for: websites, web applications, documentation with audio.

```html
<!-- Direct playback -->
<audio controls>
  <source src="https://tts-uzbek.onrender.com/tts.mp3?q=Salom%20dunyo&voice=madina" type="audio/mpeg">
</audio>

<!-- JavaScript-driven playback -->
<button onclick="speak('Salom dunyo')">🔊 Listen</button>

<script>
function speak(text) {
    const url = `https://tts-uzbek.onrender.com/tts.mp3?q=${encodeURIComponent(text)}`;
    new Audio(url).play();
}
</script>
```

### Pattern 4: Telegram Bot Integration

Best for: bots that need to reply with voice messages.

```python
import requests
import io

def send_voice_message(bot_token, chat_id, text, voice="madina"):
    """Generate TTS audio and send as a Telegram voice message."""
    # Generate audio
    audio_response = requests.get(
        "https://tts-uzbek.onrender.com/tts.mp3",
        params={"q": text, "voice": voice},
        timeout=30
    )
    audio_response.raise_for_status()

    # Send as voice message
    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendVoice",
        data={"chat_id": chat_id},
        files={"voice": ("speech.mp3", io.BytesIO(audio_response.content), "audio/mpeg")}
    )
```

### Pattern 5: Discord Bot Integration

Best for: Discord bots with voice or text channel audio.

```javascript
import { Client, GatewayIntentBits } from "discord.js";

const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages] });

client.on("messageCreate", async (message) => {
    if (message.content.startsWith("!speak ")) {
        const text = message.content.slice(7);
        const url = `https://tts-uzbek.onrender.com/tts.mp3?q=${encodeURIComponent(text)}&voice=sardor`;

        const response = await fetch(url);
        const buffer = Buffer.from(await response.arrayBuffer());

        await message.reply({
            files: [{ attachment: buffer, name: "speech.mp3" }]
        });
    }
});
```

### Pattern 6: Long Text Splitting

Best for: texts exceeding the 5000 character limit.

```python
import requests
from pathlib import Path

def split_text(text, max_length=4500):
    """Split text into chunks at sentence boundaries."""
    chunks = []
    current = ""

    for sentence in text.replace(". ", ".\n").split("\n"):
        if len(current) + len(sentence) + 1 > max_length:
            if current:
                chunks.append(current.strip())
            current = sentence
        else:
            current += " " + sentence if current else sentence

    if current:
        chunks.append(current.strip())

    return chunks

def generate_long_audio(text, voice="madina", output_dir="audio_parts"):
    """Generate audio for text of any length by splitting into chunks."""
    Path(output_dir).mkdir(exist_ok=True)
    chunks = split_text(text)
    files = []

    for i, chunk in enumerate(chunks):
        output_file = f"{output_dir}/part_{i+1:03d}.mp3"
        response = requests.get(
            "https://tts-uzbek.onrender.com/tts.mp3",
            params={"q": chunk, "voice": voice},
            timeout=30
        )
        response.raise_for_status()
        Path(output_file).write_bytes(response.content)
        files.append(output_file)
        print(f"Generated: {output_file} ({len(chunk)} chars)")

    return files
```
