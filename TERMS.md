# Terms of Service — Uzbekcha TTS

**Last Updated:** November 2026

These Terms of Service ("Terms") govern your use of the Uzbekcha TTS text-to-speech service ("Service") available at [https://tts-uzbek.onrender.com](https://tts-uzbek.onrender.com) and via its API endpoints.

By using the Service, you agree to these Terms. If you do not agree, please do not use the Service.

---

## Table of Contents

- [1. Service Description](#1-service-description)
- [2. Free Service — No Warranty](#2-free-service--no-warranty)
- [3. Acceptable Use](#3-acceptable-use)
- [4. Prohibited Uses](#4-prohibited-uses)
- [5. Rate Limits](#5-rate-limits)
- [6. Availability and Uptime](#6-availability-and-uptime)
- [7. Third-Party Voice Technology](#7-third-party-voice-technology)
- [8. Generated Audio — Ownership and Rights](#8-generated-audio--ownership-and-rights)
- [9. Content Guidelines](#9-content-guidelines)
- [10. Modifications to the Service](#10-modifications-to-the-service)
- [11. Termination and Access Restrictions](#11-termination-and-access-restrictions)
- [12. Limitation of Liability](#12-limitation-of-liability)
- [13. Indemnification](#13-indemnification)
- [14. Changes to These Terms](#14-changes-to-these-terms)
- [15. Contact](#15-contact)

---

## 1. Service Description

Uzbekcha TTS is a free, open-source text-to-speech service that converts text into spoken audio (MP3 format). The Service supports multiple languages including Uzbek, Russian, English, Turkish, and Kazakh, powered by Microsoft Edge Neural TTS technology.

The Service includes:

- A web interface for interactive text-to-speech conversion
- REST API endpoints for programmatic access
- A Telegram bot for speech generation via Telegram

---

## 2. Free Service — No Warranty

**The Service is provided completely free of charge.**

THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, ACCURACY, OR NON-INFRINGEMENT.

We do not guarantee:

- That the Service will be available at all times or without interruption
- That the Service will be free of errors, bugs, or security vulnerabilities
- That the audio output will be accurate, natural-sounding, or suitable for any specific purpose
- That the Service will continue to exist indefinitely
- That response times will meet any particular performance standard

---

## 3. Acceptable Use

You may use the Service for any lawful purpose, including but not limited to:

- **Personal projects:** Generating audio for personal use, learning, or entertainment
- **Educational use:** Language learning, accessibility tools, educational content
- **Commercial projects:** Integrating TTS into applications, websites, or products (subject to Microsoft's TTS terms)
- **Open-source projects:** Building tools and applications that use the API
- **Accessibility:** Creating audio versions of text content for visually impaired users
- **Bot integrations:** Telegram bots, Discord bots, and other messaging platform integrations

---

## 4. Prohibited Uses

You may **not** use the Service to:

- **Generate illegal content:** Create audio for content that is illegal in your jurisdiction
- **Impersonate individuals:** Generate audio designed to impersonate real people for deceptive purposes (deepfakes, fraud, scams)
- **Harass or threaten:** Create audio intended to harass, threaten, bully, or intimidate others
- **Spam or abuse:** Send automated requests designed to overwhelm, degrade, or disrupt the Service
- **Circumvent rate limits:** Use multiple IP addresses, proxies, or other methods to bypass rate limiting
- **Generate hate speech:** Create audio containing hate speech, incitement to violence, or discriminatory content
- **Phishing or fraud:** Use generated audio in phishing attacks, social engineering, or financial fraud
- **Attack the infrastructure:** Attempt to exploit vulnerabilities, perform DDoS attacks, or compromise the server

---

## 5. Rate Limits

To ensure fair access for all users, the following rate limits apply:

| Limit | Value |
|-------|-------|
| **Requests per minute** | 40 per IP address |
| **Maximum text length** | 5000 characters per request |
| **Cached requests** | Do not count against the rate limit |

If you exceed the rate limit:

- You will receive an HTTP `429 Too Many Requests` response
- The `Retry-After` header will indicate how many seconds to wait (typically 10 seconds)
- Continued abuse may result in temporary or permanent IP blocking

Rate limits are designed to be generous for normal use. If you have a legitimate need for higher limits, please contact us through GitHub Issues.

---

## 6. Availability and Uptime

**The Service runs on a free hosting tier (Render free plan) and we do not guarantee any level of uptime or availability.**

You should be aware that:

- The server may experience **cold starts** after periods of inactivity (the free tier spins down idle services)
- The Service may be **temporarily unavailable** during deployments, maintenance, or hosting provider outages
- **No SLA (Service Level Agreement)** is provided
- We will make reasonable efforts to keep the Service running, but we have no obligation to do so
- The hosting provider (Render) may change their free tier policies at any time, which could affect Service availability

**Do not rely on this Service for mission-critical applications** unless you are prepared to handle outages gracefully.

---

## 7. Third-Party Voice Technology

The speech synthesis is powered by **Microsoft Edge Neural TTS** technology. By using this Service, you acknowledge that:

- The voice technology is owned by Microsoft Corporation
- Your text is processed through Microsoft's TTS engine
- Microsoft's own terms of service and usage policies apply to the underlying TTS technology
- We do not own, control, or have any special license for the voice models
- Changes to Microsoft's TTS service or policies may affect the availability or behavior of voices
- Voice quality, available voices, and supported languages are determined by Microsoft and may change without notice

---

## 8. Generated Audio — Ownership and Rights

### No Ownership Claim by Uzbekcha TTS

**We do not claim any ownership or rights over audio generated through the Service.** The generated audio is the result of your text input processed through Microsoft's TTS engine.

### Your Responsibilities

- You are responsible for ensuring your use of the generated audio complies with applicable laws and Microsoft's TTS terms of use
- You are responsible for the content of the text you submit for synthesis
- You may use generated audio in your projects, but you do so at your own risk
- We make no representations about the intellectual property rights of the generated audio

### No Guarantee of Rights

We cannot guarantee that the generated audio is free from third-party intellectual property claims. The voice models are the property of Microsoft, and their use may be subject to Microsoft's licensing terms.

---

## 9. Content Guidelines

While we do not actively monitor or review the text submitted for synthesis, we expect users to exercise good judgment and adhere to the following guidelines:

### Do

- Use appropriate, respectful language
- Generate audio for legitimate purposes
- Respect the rights and dignity of others
- Follow the laws of your jurisdiction

### Do Not

- Submit text containing explicit threats of violence
- Generate audio of content that sexualizes minors
- Create audio for the purpose of fraud or deception
- Submit text that constitutes illegal content in your jurisdiction
- Use the Service to generate content that violates others' rights

We reserve the right to implement content filtering or moderation in the future if abuse is detected.

---

## 10. Modifications to the Service

We reserve the right to, at any time and without prior notice:

- **Modify** the Service, including changing API endpoints, parameters, response formats, or behavior
- **Add or remove features**, voices, languages, or styles
- **Change rate limits** or impose new usage restrictions
- **Discontinue** the Service entirely, either temporarily or permanently
- **Change the hosting** provider, URL, or deployment configuration

We will make reasonable efforts to communicate significant changes through the GitHub repository, but we are under no obligation to provide advance notice.

---

## 11. Termination and Access Restrictions

We reserve the right to restrict or terminate access to the Service for any user or IP address that:

- Violates these Terms of Service
- Engages in abusive, fraudulent, or harmful behavior
- Circumvents rate limits or other usage restrictions
- Causes disruption to the Service or its infrastructure

Access restrictions may be implemented without prior notice. We are not obligated to provide reasons for any restriction or termination.

---

## 12. Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW:

- IN NO EVENT SHALL THE UZBEKCHA TTS SERVICE, ITS DEVELOPERS, CONTRIBUTORS, OR AFFILIATES BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING FROM YOUR USE OF THE SERVICE
- OUR TOTAL LIABILITY FOR ANY CLAIMS ARISING FROM YOUR USE OF THE SERVICE SHALL NOT EXCEED ZERO DOLLARS ($0.00), REFLECTING THE FREE NATURE OF THE SERVICE
- WE ARE NOT LIABLE FOR ANY DAMAGES RESULTING FROM SERVICE OUTAGES, DATA LOSS, INACCURATE AUDIO GENERATION, OR ANY OTHER FAILURE OF THE SERVICE

---

## 13. Indemnification

You agree to indemnify and hold harmless the Uzbekcha TTS developers, contributors, and affiliates from any claims, damages, losses, or expenses (including reasonable legal fees) arising from:

- Your use of the Service
- Your violation of these Terms
- Your violation of any third-party rights
- Content you generate using the Service

---

## 14. Changes to These Terms

We may update these Terms from time to time. Changes will be reflected by updating the "Last Updated" date at the top of this document.

Since the Service requires no user accounts, we cannot directly notify users of changes. Continued use of the Service after changes are posted constitutes acceptance of the revised Terms.

We encourage you to review these Terms periodically.

---

## 15. Contact

For questions about these Terms of Service:

- **GitHub Issues:** [https://github.com/developer-uzbek/tts-uzbek/issues](https://github.com/developer-uzbek/tts-uzbek/issues)
- **Repository:** [https://github.com/developer-uzbek/tts-uzbek](https://github.com/developer-uzbek/tts-uzbek)

---

*These Terms of Service are provided for the Uzbekcha TTS open-source project. The Service is provided free of charge with no guarantees. Use at your own discretion and risk.*
