# Security Policy — Uzbekcha TTS

This document describes the security practices, architecture, and vulnerability reporting procedures for the Uzbekcha TTS service.

---

## Table of Contents

- [Reporting Vulnerabilities](#reporting-vulnerabilities)
- [Authentication Model](#authentication-model)
- [Input Validation](#input-validation)
- [Rate Limiting](#rate-limiting)
- [Data Handling and Storage](#data-handling-and-storage)
- [Environment Variables and Secrets](#environment-variables-and-secrets)
- [CORS Configuration](#cors-configuration)
- [Dependency Management](#dependency-management)
- [Transport Security](#transport-security)
- [Infrastructure Security](#infrastructure-security)
- [Known Limitations](#known-limitations)
- [Security Best Practices for API Consumers](#security-best-practices-for-api-consumers)

---

## Reporting Vulnerabilities

If you discover a security vulnerability in the Uzbekcha TTS service, please report it through one of the following channels:

### Preferred: GitHub Issues

Open an issue at: [https://github.com/developer-uzbek/tts-uzbek/issues](https://github.com/developer-uzbek/tts-uzbek/issues)

**For sensitive or critical vulnerabilities**, please:

1. Create a GitHub issue with the title prefix `[SECURITY]`
2. Describe the vulnerability without including exploit details in the public issue
3. Include steps to reproduce the issue if possible
4. Specify the potential impact and severity in your assessment

### What to Include in a Report

- **Description:** Clear explanation of the vulnerability
- **Impact:** What an attacker could achieve by exploiting it
- **Reproduction steps:** How to trigger the vulnerability
- **Environment:** Browser, OS, or tools used when discovering the issue
- **Suggested fix:** If you have a recommendation (optional)

### Response Timeline

As an open-source project maintained by volunteers, we aim to:

- Acknowledge vulnerability reports within **72 hours**
- Provide an initial assessment within **1 week**
- Deploy fixes for critical vulnerabilities as quickly as possible

We appreciate responsible disclosure and will credit reporters in the changelog (unless anonymity is requested).

---

## Authentication Model

**The Uzbekcha TTS API requires no authentication.** It is a public, open API by design.

### Implications

| Aspect | Status |
|--------|--------|
| API keys | Not required |
| OAuth/tokens | Not used |
| User accounts | Do not exist |
| Session management | Not applicable |
| Password storage | Not applicable |

### Rationale

The Service is designed as a free, open utility. Authentication was intentionally omitted to:

- Minimize barriers to use
- Eliminate password and credential storage risks
- Simplify the integration process for developers and AI agents
- Reduce the attack surface (no auth system to exploit)

### Trade-offs

Without authentication:

- We cannot attribute requests to individual users
- Rate limiting is IP-based only
- We cannot revoke access to individual users (only IP-based blocks)
- All API features are available to all users equally

---

## Input Validation

All user-supplied input is validated before processing.

### Text Input (`q` / `text` parameter)

| Validation | Description |
|------------|-------------|
| **Required** | Text parameter must be present and non-empty |
| **Maximum length** | 5000 characters |
| **Encoding** | UTF-8 expected; URL encoding for query parameters |
| **Sanitization** | Text is passed to the TTS engine as-is (the engine handles text-to-speech conversion) |

If text exceeds 5000 characters, the API returns `413 Payload Too Large`.

### Voice Parameter

| Validation | Description |
|------------|-------------|
| **Allowlist** | Voice IDs are validated against a known list of supported voices |
| **Case handling** | Short names are matched case-insensitively |
| **Default** | If an invalid voice is specified, the API returns `400 Bad Request` |

### Style Parameter

| Validation | Description |
|------------|-------------|
| **Allowlist** | Styles are validated against: `natural`, `deep`, `chipmunk`, `hype`, `calm` |
| **Default** | Falls back to `natural` if not specified |
| **Invalid values** | Returns `400 Bad Request` |

### Numeric Parameters (rate, pitch, volume)

| Validation | Description |
|------------|-------------|
| **Type checking** | Must be valid numbers |
| **Range** | Bounded to reasonable values by the TTS engine |

---

## Rate Limiting

Rate limiting protects the Service from abuse and ensures fair access.

| Property | Value |
|----------|-------|
| **Limit** | 40 requests per minute per IP address |
| **Scope** | New text generations only (cached responses are free) |
| **Tracking** | In-memory, IP-based counters |
| **Response** | HTTP `429 Too Many Requests` with `Retry-After: 10` header |
| **Persistence** | Counters reset when the server restarts |

### Implementation Details

- Rate limit counters are stored in application memory (not in a database)
- Counters use a rolling window approach
- Requests served from cache do not increment the counter
- The rate limiting mechanism does not store or log the content of requests

---

## Data Handling and Storage

### No Personal Data Storage

The Service does not store personal data:

| Data Type | Stored? | Details |
|-----------|---------|---------|
| User text | **No** | Processed in memory, immediately discarded after audio generation |
| Generated audio | **Temporarily** | In-memory cache only, cleared on server restart |
| IP addresses | **No** | Used for rate limiting counters in memory; not logged by the application |
| User accounts | **N/A** | No accounts exist |
| Cookies | **No** | No cookies are set by the application |
| Local storage data | **Client-side only** | UI preferences stored in the user's browser, never sent to server |

### No Database

The web service does not use a persistent database. All data exists only in application memory and is lost when the server process restarts.

### Telegram Bot Data

The Telegram bot component stores user IDs for bot functionality. This data is limited to Telegram-specific identifiers and is used solely for delivering responses.

---

## Environment Variables and Secrets

### Secrets Management

Any sensitive configuration values (such as API tokens for the Telegram bot) are managed through environment variables:

| Practice | Status |
|----------|--------|
| Secrets in environment variables | ✅ Yes |
| Secrets in source code | ❌ No — never committed to the repository |
| `.env` file in production | Managed by hosting platform (Render) |
| `.env` in version control | Excluded via `.gitignore` |

### Environment Variable Security

- Environment variables are set through the Render hosting dashboard
- They are encrypted at rest by the hosting provider
- They are not exposed through any API endpoint
- The application does not echo or log environment variable values

---

## CORS Configuration

### Cross-Origin Resource Sharing (CORS)

The API is configured to allow cross-origin requests to support browser-based integrations:

| Header | Value | Purpose |
|--------|-------|---------|
| `Access-Control-Allow-Origin` | `*` | Allows requests from any origin |
| `Access-Control-Allow-Methods` | `GET, POST, OPTIONS` | Permitted HTTP methods |
| `Access-Control-Allow-Headers` | `Content-Type` | Permitted request headers |

### CORS Security Considerations

- The permissive CORS policy (`*`) is intentional for a public API
- Since there is no authentication, CORS restrictions would not provide meaningful security benefit
- The API does not use cookies or sessions, so CSRF attacks are not applicable
- API consumers should implement their own security measures appropriate to their application

---

## Dependency Management

### Package Dependencies

| Practice | Status |
|----------|--------|
| Dependencies pinned to specific versions | ✅ Recommended |
| Regular dependency updates | ✅ Periodic review |
| Known vulnerability scanning | ✅ Via GitHub Dependabot and `npm audit` / `pip audit` |
| Minimal dependency footprint | ✅ Only essential packages |

### Update Process

1. Dependencies are reviewed periodically for known vulnerabilities
2. GitHub Dependabot alerts are monitored for the repository
3. Critical security patches are applied as soon as practical
4. Non-critical updates are batched into regular maintenance releases

---

## Transport Security

### HTTPS

| Property | Value |
|----------|-------|
| **Protocol** | HTTPS (TLS) enforced by the hosting platform |
| **Certificate** | Managed by Render (automatic Let's Encrypt certificates) |
| **HTTP redirect** | HTTP requests are redirected to HTTPS by Render |
| **Minimum TLS version** | Determined by Render's infrastructure (typically TLS 1.2+) |

All communication between clients and the Service is encrypted in transit via HTTPS. The TLS certificate is automatically provisioned and renewed by the hosting provider.

---

## Infrastructure Security

### Hosting (Render)

| Property | Value |
|----------|-------|
| **Provider** | Render ([render.com](https://render.com)) |
| **Deployment** | Automated from GitHub repository |
| **Isolation** | Containerized execution environment |
| **Network** | Behind Render's edge network and CDN |
| **Access** | No direct SSH access to production containers |

### Source Code

| Property | Value |
|----------|-------|
| **Repository** | Public on GitHub |
| **Branch protection** | Main branch protection recommended |
| **Deployment trigger** | Automatic on push to main branch |

---

## Known Limitations

The following are known security limitations of the Service. They are accepted trade-offs given the project's nature as a free, open utility:

### 1. No Authentication or Authorization

- **Risk:** Any user can access any endpoint without restriction
- **Mitigation:** Rate limiting, input validation
- **Rationale:** Authentication would add complexity and barriers to a free service

### 2. IP-Based Rate Limiting Only

- **Risk:** Users behind shared IP addresses (corporate NATs, VPNs) share rate limit quotas. Conversely, attackers can rotate IPs to bypass limits.
- **Mitigation:** Generous rate limits (40/min) reduce the impact on shared IPs
- **Rationale:** Without user accounts, IP-based limiting is the most practical approach

### 3. No Content Filtering

- **Risk:** Users can generate speech from any text, including potentially harmful content
- **Mitigation:** This is a text-to-speech service, not a content platform; generated audio is returned only to the requester
- **Rationale:** Content filtering in a multilingual context (5 languages) is complex and may create false positives

### 4. Free Hosting Tier

- **Risk:** The free tier has resource limitations that could affect availability under heavy load
- **Mitigation:** In-memory caching reduces load; rate limiting prevents abuse
- **Rationale:** The project is free and community-driven

### 5. Third-Party TTS Engine Dependency

- **Risk:** The Service depends on Microsoft Edge TTS, which could change its terms, API, or availability
- **Mitigation:** The modular architecture allows swapping TTS engines if needed
- **Rationale:** Microsoft Edge TTS provides high-quality, multilingual neural voices at no cost

### 6. In-Memory State Loss on Restart

- **Risk:** Rate limit counters and audio cache are lost when the server restarts
- **Mitigation:** This is acceptable — rate limiting resets benefit users, and cache regeneration is automatic
- **Rationale:** No persistent state eliminates database security concerns

---

## Security Best Practices for API Consumers

If you are integrating the Uzbekcha TTS API into your own application, we recommend the following security practices:

1. **Validate text input** on your side before forwarding to the TTS API — don't let users submit arbitrary text through your service without review
2. **Implement your own rate limiting** in your application to control costs and prevent abuse of your integration
3. **Use HTTPS** for all requests to the API (the base URL already uses HTTPS)
4. **Do not cache audio in publicly accessible storage** unless you've validated the content
5. **Handle errors gracefully** — do not expose raw API error messages to your end users
6. **Set timeouts** on HTTP requests to the API to prevent your application from hanging
7. **Validate audio responses** before serving to your users — check Content-Type and file size

---

*This security policy is a living document and will be updated as the project evolves. If you have suggestions for improving the security of the Uzbekcha TTS service, please open an issue on GitHub.*
