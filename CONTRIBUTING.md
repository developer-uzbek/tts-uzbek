# Contributing to Uzbekcha TTS

Thank you for your interest in contributing to Uzbekcha TTS! This guide will help you get started with development, understand the project structure, and submit your contributions.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Code Style Guidelines](#code-style-guidelines)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Reporting Issues](#reporting-issues)
- [Development Tips](#development-tips)

---

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18 or later recommended) — [Download](https://nodejs.org/)
- **npm** (comes with Node.js) or **yarn**
- **Git** — [Download](https://git-scm.com/)
- A code editor (VS Code recommended)

### Fork and Clone

1. **Fork** the repository on GitHub: [https://github.com/developer-uzbek/tts-uzbek](https://github.com/developer-uzbek/tts-uzbek)

2. **Clone** your fork locally:

   ```bash
   git clone https://github.com/YOUR-USERNAME/tts-uzbek.git
   cd tts-uzbek
   ```

3. **Add the upstream remote** to stay in sync:

   ```bash
   git remote add upstream https://github.com/developer-uzbek/tts-uzbek.git
   ```

---

## Development Environment Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Variables

Create a `.env` file in the project root for local development:

```bash
cp .env.example .env
```

If no `.env.example` exists, create `.env` with the following (adjust as needed):

```env
PORT=3000
NODE_ENV=development
```

> **Note:** Never commit your `.env` file. It is already listed in `.gitignore`.

### 3. Verify Setup

Start the development server and verify it works:

```bash
npm start
```

Then visit [http://localhost:3000](http://localhost:3000) in your browser. You should see the Uzbekcha TTS web interface.

Test the API:

```bash
curl http://localhost:3000/health
# Expected: OK

curl -o test.mp3 "http://localhost:3000/tts.mp3?q=Salom"
# Should create a valid MP3 file
```

---

## Project Structure

```
tts-uzbek/
├── server.js              # Main application entry point (Express server)
├── config.js              # Centralized configuration (voices, styles, limits, metadata)
├── package.json           # Node.js dependencies and scripts
├── .env                   # Environment variables (not committed)
├── .gitignore             # Git ignore rules
│
├── public/                # Static frontend assets
│   ├── index.html         # Main web interface (single-page app)
│   ├── styles.css         # Stylesheet for the web interface
│   ├── script.js          # Frontend JavaScript (TTS controls, UI logic)
│   ├── favicon.ico        # Site favicon
│   ├── robots.txt         # Search engine crawler rules
│   ├── sitemap.xml        # SEO sitemap
│   ├── llms.txt           # AI/LLM discovery file
│   ├── openapi.json       # OpenAPI specification
│   └── .well-known/
│       └── ai-plugin.json # AI plugin manifest
│
├── docs/                  # Documentation files
│   ├── AI_USAGE.md        # AI integration guide
│   ├── AI_API_GUIDE.md    # AI-focused API reference
│   ├── API.md             # Developer API documentation
│   ├── PRIVACY.md         # Privacy policy
│   ├── TERMS.md           # Terms of service
│   ├── SECURITY.md        # Security policy
│   ├── CONTRIBUTING.md    # This file
│   └── CHANGELOG.md       # Version history
│
├── README.md              # Project overview and quick start
├── LICENSE                 # Project license
└── render.yaml            # Render deployment configuration
```

### Key Files

| File | Description |
|------|-------------|
| `server.js` | Express.js application with all API routes, TTS generation logic, caching, and rate limiting |
| `config.js` | Centralized configuration for voices, styles, limits, SEO metadata, and application settings |
| `public/index.html` | The complete web interface — a single HTML file with embedded or linked CSS/JS |
| `public/script.js` | Frontend logic for the TTS controls, audio playback, voice selection, and history management |

---

## Running the Application

### Development Mode

```bash
npm start
```

This starts the server on `http://localhost:3000` (or the port specified in your `.env` file).

### With Auto-Restart (using nodemon)

If you have `nodemon` installed:

```bash
npx nodemon server.js
```

This will automatically restart the server when you save changes to `.js` files.

### Production Mode

```bash
NODE_ENV=production node server.js
```

---

## Running Tests

### Manual API Testing

Use cURL to test the API endpoints:

```bash
# Health check
curl http://localhost:3000/health

# List voices
curl http://localhost:3000/api/voices | python -m json.tool

# Service info
curl http://localhost:3000/api/info | python -m json.tool

# Generate audio (GET)
curl -o test.mp3 "http://localhost:3000/tts.mp3?q=Salom%20dunyo&voice=sardor"

# Generate audio (POST)
curl -X POST http://localhost:3000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Salom dunyo", "voice": "sardor"}' \
  -o test.mp3

# Verify the MP3 file is valid
file test.mp3
```

### Automated Tests

If automated tests are available:

```bash
npm test
```

### Writing Tests

When adding new features, please include tests that cover:

- **Happy path:** Normal, expected usage
- **Edge cases:** Empty text, maximum length text, special characters
- **Error cases:** Invalid voices, invalid styles, exceeding rate limits
- **API contract:** Correct response headers, status codes, and content types

---

## Code Style Guidelines

### General Principles

1. **Keep it simple** — this is a focused utility project. Avoid unnecessary abstraction.
2. **Be consistent** — follow the patterns established in the existing codebase.
3. **Comment your intent** — explain *why*, not just *what*. The code shows what; comments should explain why.
4. **Handle errors** — always handle potential errors gracefully. Don't let the server crash.

### JavaScript Style

- **Use modern JavaScript:** ES6+ features (arrow functions, `const`/`let`, template literals, destructuring)
- **Semicolons:** Use semicolons at the end of statements
- **Quotes:** Use single quotes for strings (`'hello'`), or template literals for interpolation (`` `Hello ${name}` ``)
- **Indentation:** 2 spaces (consistent with the existing codebase)
- **Variable naming:** Use `camelCase` for variables and functions, `UPPER_SNAKE_CASE` for constants
- **File naming:** Use `kebab-case` for filenames (e.g., `rate-limiter.js`)

### Example

```javascript
const express = require('express');
const app = express();

const MAX_TEXT_LENGTH = 5000;
const DEFAULT_VOICE = 'uz-UZ-MadinaNeural';

app.get('/tts.mp3', async (req, res) => {
  const text = req.query.q;

  if (!text || text.trim().length === 0) {
    return res.status(400).send('Missing text parameter');
  }

  if (text.length > MAX_TEXT_LENGTH) {
    return res.status(413).send(`Text too long. Maximum: ${MAX_TEXT_LENGTH} characters`);
  }

  try {
    const audio = await generateAudio(text, DEFAULT_VOICE);
    res.set('Content-Type', 'audio/mpeg');
    res.send(audio);
  } catch (error) {
    console.error('TTS generation failed:', error.message);
    res.status(502).send('TTS engine error');
  }
});
```

### HTML/CSS Style

- Use semantic HTML elements where appropriate
- Keep CSS in separate files (or in `<style>` blocks for single-file components)
- Use CSS custom properties (variables) for colors and spacing
- Ensure responsive design — the UI should work on mobile devices

### Documentation Style

- Use clear, concise language
- Include code examples for technical documentation
- Keep markdown formatting consistent with existing docs
- Use tables for structured data

---

## Submitting Pull Requests

### Before You Start

1. **Check existing issues** — look for open issues related to your planned change
2. **Open an issue first** for significant changes to discuss the approach before investing time in implementation
3. **Keep PRs focused** — one feature or fix per pull request

### PR Workflow

1. **Create a branch** from the latest `main`:

   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** — follow the code style guidelines above.

3. **Test your changes** locally:

   ```bash
   npm start
   # Test your changes manually or with automated tests
   ```

4. **Commit your changes** with clear, descriptive messages:

   ```bash
   git add .
   git commit -m "feat: add support for new voice style 'whisper'"
   ```

   Use conventional commit prefixes:
   - `feat:` — new features
   - `fix:` — bug fixes
   - `docs:` — documentation changes
   - `style:` — code style changes (formatting, no logic change)
   - `refactor:` — code restructuring without changing behavior
   - `perf:` — performance improvements
   - `chore:` — maintenance tasks (dependency updates, config changes)

5. **Push to your fork:**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** on GitHub from your fork to the upstream `main` branch.

### PR Description Template

When opening a PR, include:

```markdown
## Summary
Brief description of what this PR does.

## Changes
- List of specific changes made

## Testing
- How you tested these changes
- Any manual testing steps

## Screenshots (if UI changes)
Before/after screenshots if applicable.

## Related Issues
Closes #XX (if applicable)
```

### What We Look For in a PR

- ✅ Code follows the project's style guidelines
- ✅ Changes are focused and well-scoped
- ✅ Existing functionality is not broken
- ✅ Error handling is included for new code paths
- ✅ Documentation is updated if the public API changes
- ✅ Commit messages are clear and descriptive

---

## Reporting Issues

### Bug Reports

When reporting a bug, please include:

1. **Title:** Clear, concise summary of the issue
2. **Description:** Detailed explanation of the bug
3. **Steps to Reproduce:**
   - Step-by-step instructions to trigger the bug
   - Include the exact API request if applicable (URL, parameters, headers)
4. **Expected Behavior:** What should have happened
5. **Actual Behavior:** What actually happened
6. **Environment:**
   - Browser and version (for web interface issues)
   - OS (for API/server issues)
   - Node.js version (if running locally)
7. **Screenshots or Logs:** If applicable

### Feature Requests

For feature requests, please include:

1. **Title:** Clear description of the desired feature
2. **Use Case:** Why this feature would be valuable
3. **Proposed Solution:** How you envision it working (if you have ideas)
4. **Alternatives Considered:** Other approaches you've thought of

### Issue Labels

| Label | Description |
|-------|-------------|
| `bug` | Something isn't working correctly |
| `feature` | New feature request |
| `enhancement` | Improvement to existing functionality |
| `documentation` | Documentation updates needed |
| `good first issue` | Good for newcomers to the project |
| `help wanted` | Extra attention is needed |
| `security` | Security-related issues |

---

## Development Tips

### Testing Different Voices

Use these quick commands to test all available voices:

```bash
for voice in sardor madina dmitry svetlana andrew aria ahmet emel daulet aigul; do
  echo "Testing: $voice"
  curl -s -o "test_${voice}.mp3" "http://localhost:3000/tts.mp3?q=Salom%20dunyo&voice=${voice}"
done
```

### Testing Styles

```bash
for style in natural deep chipmunk hype calm; do
  echo "Testing style: $style"
  curl -s -o "test_${style}.mp3" "http://localhost:3000/tts.mp3?q=Salom%20dunyo&style=${style}"
done
```

### Checking Rate Limiting

```bash
# Send rapid requests to test rate limiting
for i in $(seq 1 45); do
  status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/tts.mp3?q=Test%20${i}")
  echo "Request $i: HTTP $status"
done
```

### Debugging

Set the `NODE_ENV` to `development` for more verbose logging:

```bash
NODE_ENV=development npm start
```

### Useful VS Code Extensions

- **REST Client** — for testing API endpoints directly in VS Code
- **ESLint** — for JavaScript linting
- **Prettier** — for code formatting
- **Thunder Client** — lightweight API client

---

## Thank You!

Every contribution makes Uzbekcha TTS better for the community. Whether it's fixing a typo, reporting a bug, or implementing a new feature — your help is appreciated!

If you have questions that aren't covered in this guide, please open a GitHub issue and we'll be happy to help.

**GitHub Repository:** [https://github.com/developer-uzbek/tts-uzbek](https://github.com/developer-uzbek/tts-uzbek)
