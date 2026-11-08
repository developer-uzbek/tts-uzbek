# Privacy Policy — Uzbekcha TTS

**Last Updated:** November 2026

This privacy policy describes how the Uzbekcha TTS service ("Service", "we", "our") handles information when you use our text-to-speech API and web interface at [https://tts-uzbek.onrender.com](https://tts-uzbek.onrender.com).

---

## Table of Contents

- [Overview](#overview)
- [No Account Required](#no-account-required)
- [Information We Do Not Collect](#information-we-do-not-collect)
- [Text Processing](#text-processing)
- [Audio Caching](#audio-caching)
- [Cookies and Local Storage](#cookies-and-local-storage)
- [Server Logs](#server-logs)
- [Third-Party Services](#third-party-services)
- [Telegram Bot Data](#telegram-bot-data)
- [Data Retention](#data-retention)
- [Children's Privacy](#childrens-privacy)
- [Changes to This Policy](#changes-to-this-policy)
- [Contact](#contact)

---

## Overview

Uzbekcha TTS is designed with privacy as a priority. We operate on a principle of minimal data collection:

- **No user accounts or registration** are required to use the service
- **No personal data is stored** — text is processed in memory and discarded
- **No databases** store web user information
- **No tracking cookies** are used
- **No analytics platforms** track your usage

---

## No Account Required

The Uzbekcha TTS service is completely free and requires no account, registration, email address, phone number, or any other personal information to use. You can use the API and web interface anonymously.

---

## Information We Do Not Collect

We explicitly **do not** collect, store, or process the following:

- Names, email addresses, or contact information
- Payment information or billing details
- User accounts, passwords, or authentication tokens
- Browsing history or search history
- Location data or GPS coordinates
- Device identifiers, fingerprints, or advertising IDs
- Social media profiles or linked accounts

---

## Text Processing

When you submit text for speech synthesis:

1. **In Transit:** Your text is transmitted over HTTPS (encrypted) to our server.
2. **In Memory:** The text is held temporarily in server memory only for the duration needed to generate the audio.
3. **Forwarded to TTS Engine:** The text is sent to the Microsoft Edge TTS engine for synthesis.
4. **Discarded:** After audio generation is complete, the original text is not written to disk or stored in any database.

> **Important:** We do not log, record, or store the text content you submit for synthesis. Your text exists in server memory only for the brief time required to process it.

---

## Audio Caching

To improve performance and reduce processing time for repeated requests:

- **Cache Type:** Temporary, in-memory cache only
- **Cache Duration:** Audio remains in cache while the server is running; it is cleared when the server restarts
- **Cache Scope:** The cache stores the generated audio bytes keyed by a hash of the request parameters (text, voice, style, etc.)
- **No Persistent Storage:** Cached audio is never written to disk or stored in a database
- **No User Association:** Cached entries are not associated with any user identifier, IP address, or session

The cache exists solely for performance optimization. Since the service runs on a free hosting tier, the server may restart periodically, which clears all cached data automatically.

---

## Cookies and Local Storage

### Cookies

The Uzbekcha TTS web interface **does not set any cookies** for tracking, analytics, or advertising purposes.

### Local Storage

The web interface uses the browser's `localStorage` API to save your **user preferences** locally on your device. This data:

- Is stored only in your browser, on your device
- Is never transmitted to our server
- Includes only UI preferences such as selected voice, style, and interface settings
- Can be cleared at any time through your browser settings

We do not use `localStorage` for tracking, fingerprinting, or any purpose other than preserving your UI preferences between visits.

---

## Server Logs

### Standard Hosting Logs

Our hosting provider (Render) may collect standard server access logs as part of normal platform operations. These logs may include:

- IP addresses
- Request timestamps
- Request paths (URL endpoints called)
- HTTP status codes
- User-Agent strings

These logs are managed by Render according to their own privacy policy and are not accessed by us for tracking or profiling purposes. They are used only for debugging operational issues if they arise.

### Application-Level Logging

Our application may log minimal operational information for debugging and error resolution:

- Error messages when TTS generation fails
- Rate limiting events (IP-based counters, not stored persistently)

We do not log the content of text submitted for synthesis.

---

## Third-Party Services

The Uzbekcha TTS service relies on the following third-party services:

### Microsoft Edge TTS (Speech Engine)

- **Purpose:** Converts text to speech audio
- **Data Shared:** The text you submit for synthesis is forwarded to Microsoft's Edge TTS engine
- **Microsoft's Privacy:** Text processing is subject to [Microsoft's Privacy Statement](https://privacy.microsoft.com/en-us/privacystatement)
- **Note:** We use the same TTS engine that powers Microsoft Edge's built-in read-aloud feature

### Render (Hosting Platform)

- **Purpose:** Hosts and runs the Uzbekcha TTS service
- **Data Shared:** Standard HTTP request data (IP address, request headers, URL paths) as part of normal web hosting operations
- **Render's Privacy:** Subject to [Render's Privacy Policy](https://render.com/privacy)

### GitHub (Source Code Hosting)

- **Purpose:** Hosts the open-source code repository
- **Data Shared:** Only if you interact with the GitHub repository (issues, pull requests, etc.)
- **GitHub's Privacy:** Subject to [GitHub's Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement)

---

## Telegram Bot Data

If you interact with the Uzbekcha TTS Telegram bot:

### Data Collected

- **Telegram User ID:** Stored to associate bot interactions and provide personalized responses within the bot
- **Chat ID:** Used to send audio responses back to your chat

### Data Not Collected via Telegram

- Your phone number, profile photo, or real name are not stored by our bot
- Message content (text you send for synthesis) is processed in memory and not stored persistently

### Data Usage

Telegram user IDs are stored solely for bot functionality purposes, including:

- Delivering generated audio back to the correct chat
- Managing per-user bot settings (if applicable)

### Data Deletion

If you wish to have your Telegram user ID removed from the bot's storage, you can:

- Block the bot on Telegram (stops all future interactions)
- Contact us to request deletion (see [Contact](#contact) below)

---

## Data Retention

| Data Type | Retention Period | Storage Location |
|-----------|-----------------|------------------|
| Submitted text | None — processed in memory, immediately discarded | Server RAM only |
| Generated audio | Temporary — in-memory cache, cleared on restart | Server RAM only |
| User accounts | N/A — no accounts exist | N/A |
| Cookies | None — no cookies are set | N/A |
| localStorage preferences | Indefinite — stored on your device only | Your browser |
| Server access logs | Managed by Render hosting | Render platform |
| Telegram user IDs | Until manually deleted or bot is stopped | Bot application storage |

---

## Children's Privacy

The Uzbekcha TTS service is a general-purpose text-to-speech tool. We do not knowingly collect personal information from children under the age of 13 (or the applicable age of consent in your jurisdiction). Since the service requires no account or personal information to use, children can use it with the same privacy protections as any other user.

---

## Changes to This Policy

We may update this privacy policy from time to time. Changes will be reflected by updating the "Last Updated" date at the top of this document. Significant changes will be noted in the project's [CHANGELOG.md](CHANGELOG.md).

Since the service requires no user accounts, we have no way to directly notify users of policy changes. We encourage you to review this policy periodically.

---

## Contact

If you have questions about this privacy policy or wish to request data deletion:

- **GitHub Issues:** [https://github.com/developer-uzbek/tts-uzbek/issues](https://github.com/developer-uzbek/tts-uzbek/issues)
- **Email:** *(Contact information available on the GitHub repository)*

---

*This privacy policy is provided in good faith to describe our data handling practices. The Uzbekcha TTS service is a free, open-source project and makes no legal guarantees beyond what is described here.*
