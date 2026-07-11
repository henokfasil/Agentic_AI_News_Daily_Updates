# Agentic AI Daily Digest — by Helias AI & Analytics

A daily email newsletter bot that aggregates the latest agentic AI research, demos, and industry news — delivered every morning as a branded **Helias AI & Analytics** digest.

## What It Covers

| Source | Content |
|---|---|
| **arXiv** | Latest academic papers on agentic AI, autonomous agents, multi-agent LLMs |
| **Hugging Face** | Recently updated models and spaces tagged with AI agents |
| **Anthropic Blog** | Claude, Constitutional AI, safety research |
| **OpenAI Blog** | GPT, Assistants API, product updates |
| **Google DeepMind** | Gemini, AlphaCode, research |
| **Hugging Face Blog** | Open-source models, community highlights |
| **LangChain Blog** | Agents, RAG, orchestration frameworks |
| **Mistral AI** | Open-weight model releases |
| **The Gradient** | Long-form AI research commentary |
| **AI Snake Oil** | Critical AI analysis |

## Quick Deploy on Ubuntu VPS

```bash
# 1. Clone
git clone https://github.com/henokfasil/Agentic_AI_News_Daily_Updates.git agentic_ai_bot
cd agentic_ai_bot

# 2. Run setup (creates venv, installs deps, scaffolds .env)
chmod +x setup.sh && ./setup.sh

# 3. Add Gmail credentials
nano .env

# 4. Test — sends a real email immediately
source venv/bin/activate && python aggregator.py

# 5. Schedule daily at 7 AM UTC
crontab -e
# Add: 0 7 * * * /root/agentic_ai_bot/venv/bin/python /root/agentic_ai_bot/aggregator.py >> /root/agentic_ai_bot/cron.log 2>&1
```

## .env Setup

```
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxxxxxx
RECIPIENT_EMAIL=your@gmail.com
```

Generate an app password (requires Gmail 2FA):
https://myaccount.google.com/apppasswords

## Requirements

- Python 3.10+
- Gmail account with 2FA + app password
- Ubuntu VPS (or any Linux server with cron)

## Architecture

Single file (`aggregator.py`) — no database, no external AI APIs, no state between runs.

```
fetch_arxiv_papers()      → arXiv Atom API
fetch_huggingface_updates() → HF REST API (models + spaces)
fetch_blog_rss()          → feedparser (8 RSS feeds)
build_html()              → Helias AI & Analytics branded HTML email
send_email()              → Gmail SMTP SSL port 465
```

---

*Produced by [Helias AI & Analytics](mailto:hft4866@gmail.com)*
