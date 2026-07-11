# 🤖 Agentic AI Daily News Bot

Aggregates the latest agentic AI updates from arXiv, Hugging Face, and top AI blogs — delivered to your inbox every morning.

## Sources
- **arXiv** — latest academic papers on agentic AI, autonomous agents, multi-agent LLMs
- **Hugging Face** — recently updated models and spaces tagged with AI agents
- **Blogs** — Anthropic, OpenAI, Google DeepMind, Hugging Face, LangChain, Mistral, The Gradient

## Quick Deploy on Ubuntu VPS

```bash
# 1. Clone
git clone https://github.com/henokfasil/Agentic_AI_News_Daily_Updates.git agentic_ai_bot
cd agentic_ai_bot

# 2. Run setup
chmod +x setup.sh && ./setup.sh

# 3. Fill in credentials
nano .env

# 4. Test
source venv/bin/activate && python aggregator.py

# 5. Schedule (7 AM UTC daily)
crontab -e
# Add: 0 7 * * * /full/path/to/agentic_ai_bot/venv/bin/python /full/path/to/agentic_ai_bot/aggregator.py >> /full/path/to/agentic_ai_bot/cron.log 2>&1
```

## Gmail App Password
1. Enable 2FA on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate a password for "Mail" → paste into `.env` as `GMAIL_APP_PASSWORD`

## .env File
```
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
RECIPIENT_EMAIL=your_email@gmail.com
```
