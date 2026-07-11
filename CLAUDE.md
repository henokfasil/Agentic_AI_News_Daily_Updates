# CLAUDE.md — Agentic AI Daily News Bot

## Project Overview

Daily email digest bot that aggregates agentic AI updates and delivers them as a branded
**Helias AI & Analytics** newsletter every morning at 7 AM UTC.

**Owner:** Helias AI & Analytics  
**Repo:** https://github.com/henokfasil/Agentic_AI_News_Daily_Updates  
**VPS:** `root@72.60.133.179` (Ubuntu 24, SSH via `~/.ssh/vps_key`)  
**Python:** 3.12  
**Delivery:** Gmail SMTP → `hft4866@gmail.com`

---

## File Structure

```
aggregator.py      # Single entry-point: fetch → build HTML → send email
requirements.txt   # feedparser, requests, python-dotenv
.env               # secrets (gitignored) — see .env.example
.env.example       # template: GMAIL_USER, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL
setup.sh           # one-command VPS setup (venv + pip + .env scaffold)
README.md          # public-facing deploy guide
CLAUDE.md          # this file
```

---

## Architecture

`aggregator.py` has four logical sections:

| Function | What it does |
|---|---|
| `fetch_arxiv_papers()` | arXiv API — searches "agentic AI OR AI agent OR autonomous agent OR multi-agent LLM", returns 8 most recent |
| `fetch_huggingface_updates()` | HF REST API — 5 models + 5 spaces matching "agentic AI" / "AI agent", sorted by lastModified |
| `fetch_blog_rss()` | feedparser — 8 RSS feeds (Anthropic, OpenAI, DeepMind, HF Blog, LangChain, Mistral, AI Snake Oil, The Gradient), 2 posts each, capped at 12 |
| `build_html()` | Renders branded Helias AI & Analytics HTML email (deep navy gradient header, company tagline, intro blurb, three sections, branded footer) |
| `send_email()` | Gmail SMTP SSL port 465 |

All functions are independent — they can be called and tested individually.

---

## Branding Rules

The email must always be presented as a **Helias AI & Analytics** publication:

- Header: `Helias AI & Analytics` with tagline `Intelligence · Insight · Innovation`
- Brand colors: deep navy gradient `#0a0a23 → #1a1a6e → #2d2d9e`, accent `#7eb8f7`
- Subject line format: `Helias AI & Analytics | Agentic AI Daily Digest — {date}`
- Footer: company name, copyright, contact email `hft4866@gmail.com`
- Do **not** mention Claude, Anthropic, or any AI tool in the email body

---

## Environment Variables

```bash
GMAIL_USER=hft4866@gmail.com
GMAIL_APP_PASSWORD=<16-char Gmail app password, no spaces>
RECIPIENT_EMAIL=hft4866@gmail.com
```

Gmail app passwords require 2FA on the account. Generate at:
https://myaccount.google.com/apppasswords

---

## VPS Cron Job

Runs daily at **10:00 PM Paris time** (Europe/Paris — auto-adjusts for DST):

```
TZ=Europe/Paris
0 22 * * * /root/agentic_ai_bot/venv/bin/python /root/agentic_ai_bot/aggregator.py >> /root/agentic_ai_bot/cron.log 2>&1
```

UTC equivalent: 20:00 UTC in summer (CEST, UTC+2) · 21:00 UTC in winter (CET, UTC+1)

### Change send time
Edit crontab on VPS: `crontab -e`
The `TZ=Europe/Paris` line above the job makes the schedule interpret times in Paris timezone.
Change `0 22` to any `MM HH` in Paris local time.

Check logs: `tail -50 /root/agentic_ai_bot/cron.log`

---

## Common Tasks

### Test the bot manually
```bash
ssh root@72.60.133.179
cd /root/agentic_ai_bot && source venv/bin/activate && python aggregator.py
```

### Deploy an update
```bash
# 1. Edit aggregator.py locally, commit and push
git add aggregator.py && git commit -m "..." && git push origin main

# 2. Pull on VPS
ssh root@72.60.133.179 'cd /root/agentic_ai_bot && git pull origin main'
```

### Add a new RSS feed source
In `fetch_blog_rss()`, append to the `feeds` list:
```python
("Source Name", "https://example.com/rss.xml"),
```

### Add a new data source (e.g. YouTube, Reddit)
Add a new `fetch_*()` function, call it in `main()`, pass results to `build_html()`,
and add a renderer and section in `build_html()`.

---

## Dependencies

```
feedparser==6.0.11    # RSS/Atom parsing + arXiv API (Atom feed)
requests==2.31.0      # Hugging Face REST API calls
python-dotenv==1.0.1  # .env loading
```

No external AI API calls. No database. No state between runs.

---

## Known Constraints

- **arXiv**: Public API, no key needed. Rate limit: be polite (1 request per run is fine).
- **Hugging Face**: Public API endpoints used, no token needed for search/list.
- **Gmail SMTP**: App password (not account password). Port 465 SSL. Requires 2FA on account.
- **No deduplication**: Each run fetches fresh; the same paper may appear two days in a row if it stays at the top of arXiv results. This is acceptable for now.
- **VPS**: Hostinger Ubuntu 24 VPS. The VPS can be silently stopped by Hostinger — if cron stops firing, check VPS status first.
