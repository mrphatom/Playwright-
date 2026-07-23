# 🤖 Telegram Web Automation Bot (`tg-playwright-bot`)

![Docker Build](https://img.shields.io/badge/Docker-Build-2496ED?logo=docker&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?logo=playwright&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

A high-performance Telegram bot that spins up an isolated, headless Chromium browser environment on demand using Playwright. It navigates to target URLs, handles client-side rendering, performs browser interactions (scrolling, waiting, clicking), captures full-page screenshots, and delivers extracted data directly back to your Telegram chat.

---

## ✨ Features

- **🌐 Isolated Browser Environments:** Spawns asynchronous Chromium contexts per job to isolate browsing sessions.
- **📸 High-Res Screenshots:** Captures full-page screenshots even on complex single-page applications (SPAs).
- **⚡ Smart Dynamic Waiting:** Uses network idle checks to ensure heavy JavaScript loads completely before taking snapshots.
- **🐳 Dockerized Architecture:** Built on top of official Microsoft Playwright images to eliminate missing OS font/X11 library bugs.
- **⚙️ Automated CI/CD:** Built-in GitHub Actions workflow to auto-build and publish Docker images to GitHub Container Registry (GHCR).

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Bot Framework:** `python-telegram-bot`
- **Browser Engine:** `playwright` (Chromium)
- **Containerization:** Docker & Docker Compose
- **CI/CD:** GitHub Actions

---

## 🤖 Telegram Bot Commands

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| `/start` | None | Displays welcome message and basic usage guidelines. | `/start` |
| `/check` | `<URL>` | Launches browser, navigates to target URL, scrolls, and returns screenshot + title. | `/check https://github.com` |

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:
1. Git
2. Docker Desktop (Recommended)
3. A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Quickstart with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone [https://github.com/mrphatom/tg-playwright-bot.git](https://github.com/mrphatom/tg-playwright-bot.git)
   cd tg-playwright-bot
   ```

2. **Configure environment variables**  
   Create a `.env` file in the root directory:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ```

3. **Run with Docker Compose**
   ```bash
   docker compose up -d --build
   ```

---

### Local Development Setup (Without Docker)

<details>
<summary><b>Click here for local Python instructions</b></summary>

If you prefer to run the script natively on your machine for debugging or development:

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

3. **Run the bot**
   ```bash
   python bot.py
   ```

</details>

---

## 🔄 Automated CI/CD Deployment

This repository includes a pre-configured GitHub Actions workflow in `.github/workflows/docker-publish.yml`.

Whenever you push to the `main` branch, GitHub Actions will build the Docker container and push it to the GitHub Container Registry (GHCR).

**Pulling the pre-built image on your VPS:**

```bash
docker pull ghcr.io/mrphatom/tg-playwright-bot:latest
```

---

## 📂 Project Structure

```text
tg-playwright-bot/
├── .github/
│   └── workflows/
│       └── docker-publish.yml   # CI/CD GitHub Actions workflow
├── bot.py                       # Main bot logic & Playwright handler
├── Dockerfile                   # Docker image definition
├── docker-compose.yml           # Compose setup for deployment
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md
```

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.
