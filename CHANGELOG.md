# Changelog

All notable changes to the Uzbekcha TTS project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] — 2026-11-01

### 🎉 Complete Platform Rebrand

The project has been completely rebranded from **VoiceCraft Pro** to **Uzbekcha TTS** to better reflect its primary purpose: providing high-quality text-to-speech for the Uzbek language and Central Asian region.

- Renamed all branding references from "VoiceCraft Pro" to "Uzbekcha TTS"
- Updated page titles, meta descriptions, and heading text throughout the application
- New application identity reflects Uzbek-first focus while maintaining multilingual support
- Updated URLs and service references across all documentation and configuration

### ⚙️ New Centralized Configuration System

Introduced `config.js` — a single centralized configuration file that manages all application settings, eliminating scattered hardcoded values throughout the codebase.

- **Voice definitions:** All voice IDs, names, locales, and genders defined in one place
- **Style definitions:** All available voice styles (`natural`, `deep`, `chipmunk`, `hype`, `calm`) centrally configured
- **Rate limit settings:** Request limits, window durations, and retry delays in one location
- **Application metadata:** Service name, version, description, and URLs configurable from a single source
- **SEO metadata:** Page titles, descriptions, Open Graph tags, and structured data driven from configuration
- **AI discovery metadata:** LLMs.txt content, AI plugin manifest, and OpenAPI spec generated from config

### 🤖 AI Integration Documentation

Added comprehensive documentation specifically designed for AI assistants, LLM agents, and automated integrations.

- **AI_USAGE.md** — Complete step-by-step guide for AI assistants covering:
  - Service discovery via `/api/info`, health checks, and AI plugin files
  - Voice listing and selection
  - Audio generation with real code examples (Python, JavaScript, cURL)
  - Downloading, saving, and delivering audio to users
  - Error handling with retry logic
  - Audio verification (Content-Type, file size, MP3 magic bytes)
  - Clear explanation of platform limitations for AI chat interfaces

- **AI_API_GUIDE.md** — Full API reference written for AI agents covering:
  - Every endpoint with method, URL, parameters, and response format
  - Real request/response examples for each endpoint
  - Code examples in Python, JavaScript, and cURL
  - Voice selection guide with all methods (full ID, short name, language, gender)
  - Styles reference
  - Error handling guide with retry logic examples
  - Rate limiting explanation and optimization tips
  - Audio verification checklist and implementation

### 🎨 Premium Responsive Frontend Redesign

Complete redesign of the web interface with a modern, responsive, premium look and feel.

- Fully responsive layout that works on mobile, tablet, and desktop
- Modern UI with clean typography and intuitive controls
- Real-time audio playback with integrated audio player
- Voice selection dropdown with all 10 neural voices
- Style selector for all 5 voice styles
- Character count display with live updates and limit warnings
- Generation history with playback and re-generation
- Loading states and progress indicators
- Dark/light theme considerations
- Accessible design with proper ARIA labels and keyboard navigation
- LocalStorage-based preference persistence (no cookies)

### 🔍 SEO Optimization

Added comprehensive search engine optimization for discoverability.

- **Meta tags:** Complete Open Graph, Twitter Card, and standard meta tags
- **Structured data:** JSON-LD schema markup for the web application (WebApplication, SoftwareApplication)
- **sitemap.xml:** XML sitemap listing all public pages and endpoints
- **robots.txt:** Search engine crawler directives with sitemap reference
- **Semantic HTML:** Proper heading hierarchy, landmark regions, and semantic elements
- **Performance:** Optimized asset loading and minimal external dependencies

### 🤖 AI Discovery Files

Added standard AI discovery files for automatic integration with AI platforms and tools.

- **llms.txt** — Plain-text service summary formatted for LLM consumption, describing API endpoints, parameters, and usage examples
- **ai-plugin.json** — OpenAI ChatGPT plugin manifest at `/.well-known/ai-plugin.json` for plugin ecosystem compatibility
- **openapi.json** — Full OpenAPI 3.0 specification describing all endpoints, parameters, request/response schemas, and examples
- **`/api/info` endpoint** — Machine-readable JSON endpoint for runtime service discovery by AI agents

### 📖 Professional Documentation Suite

Added a complete set of professional documentation files.

- **API.md** — Developer-facing API documentation with:
  - Complete endpoint reference with parameters and response formats
  - Voice selection guide with all five selection methods
  - Code examples in Python, JavaScript, cURL, and PowerShell
  - Production-ready functions with full error handling
  - Integration patterns (batch processing, HTML embedding, Telegram bots, Discord bots, long text splitting)
  - Rate limiting details and error code reference

- **PRIVACY.md** — Privacy policy covering:
  - No account/registration requirement
  - No personal data storage (text processed in memory only)
  - Temporary in-memory audio caching
  - No tracking cookies (localStorage for UI preferences only)
  - Third-party service disclosures (Microsoft Edge TTS, Render hosting)
  - Telegram bot data handling
  - Data retention summary table

- **TERMS.md** — Terms of service covering:
  - Free service with no warranty
  - Acceptable and prohibited uses
  - Rate limits and enforcement
  - No guaranteed uptime (free hosting tier)
  - Third-party voice technology acknowledgment (Microsoft Edge Neural TTS)
  - Generated audio ownership (no claims by the service)
  - Right to modify or discontinue the service
  - Content guidelines
  - Limitation of liability

- **SECURITY.md** — Security policy covering:
  - Vulnerability reporting process (GitHub Issues)
  - Authentication model (public API, no auth required)
  - Input validation details (text length, voice allowlist, style allowlist)
  - Rate limiting implementation
  - Data handling practices (no personal data storage)
  - Environment variable management for secrets
  - CORS configuration
  - Dependency management and update process
  - Known limitations and accepted trade-offs
  - Security best practices for API consumers

- **CONTRIBUTING.md** — Contribution guide covering:
  - Development environment setup (Node.js, npm, Git)
  - Project structure explanation with file descriptions
  - Running the application in development and production modes
  - Testing procedures (manual cURL commands and automated tests)
  - Code style guidelines (JavaScript, HTML/CSS, documentation)
  - Pull request workflow with conventional commit format
  - Issue reporting templates (bugs and feature requests)
  - Development tips (testing voices, styles, rate limiting)

### 🔧 Technical Improvements

- Modular route organization for cleaner code structure
- Improved error messages with consistent HTTP status codes
- Enhanced caching logic for better performance
- Proper Content-Type headers on all responses
- CORS headers for cross-origin API access
- Health check endpoints (`/health`, `/ping`) for uptime monitoring

---

## [1.0.0] — Initial Release

### Added

- Text-to-speech conversion via Microsoft Edge Neural TTS
- Support for Uzbek, Russian, English, Turkish, and Kazakh languages
- 10 neural voices (male and female for each language)
- REST API with `/tts.mp3` endpoint
- Basic web interface for interactive use
- In-memory audio caching
- IP-based rate limiting
- Telegram bot integration

---

[2.0.0]: https://github.com/developer-uzbek/tts-uzbek/releases/tag/v2.0.0
[1.0.0]: https://github.com/developer-uzbek/tts-uzbek/releases/tag/v1.0.0
