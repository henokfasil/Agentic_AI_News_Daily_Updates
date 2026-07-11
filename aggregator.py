import os
import smtplib
import requests
import urllib.parse
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import feedparser

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", GMAIL_USER)


def fetch_arxiv_papers():
    query = urllib.parse.quote("agentic AI OR AI agent OR autonomous agent OR multi-agent LLM")
    url = (
        f"http://export.arxiv.org/api/query"
        f"?search_query=all:{query}&start=0&max_results=10"
        f"&sortBy=lastUpdatedDate&sortOrder=descending"
    )
    feed = feedparser.parse(url)
    papers = []
    for entry in feed.entries[:8]:
        authors = ", ".join(a.name for a in entry.get("authors", [])[:3]) or "Unknown"
        summary = entry.get("summary", "")
        papers.append({
            "title": entry.title.replace("\n", " "),
            "summary": summary[:300] + "..." if len(summary) > 300 else summary,
            "link": entry.link,
            "authors": authors,
        })
    return papers


def fetch_huggingface_updates():
    results = []
    endpoints = [
        ("Model", "https://huggingface.co/api/models?search=agentic+AI&sort=lastModified&direction=-1&limit=6"),
        ("Space", "https://huggingface.co/api/spaces?search=AI+agent&sort=lastModified&direction=-1&limit=6"),
    ]
    for kind, url in endpoints:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for item in r.json()[:5]:
                    item_id = item.get("modelId") or item.get("id", "")
                    base = "spaces" if kind == "Space" else ""
                    link = f"https://huggingface.co/{base}/{item_id}".replace("//", "/").replace("https:/", "https://")
                    results.append({"type": kind, "name": item_id, "link": link})
        except Exception as e:
            print(f"HF {kind} error: {e}")
    return results


def fetch_blog_rss():
    feeds = [
        ("Anthropic", "https://www.anthropic.com/feed.xml"),
        ("OpenAI", "https://openai.com/blog/rss.xml"),
        ("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
        ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
        ("LangChain", "https://blog.langchain.dev/rss/"),
        ("Mistral AI", "https://mistral.ai/fr/news/rss.xml"),
        ("AI Snake Oil", "https://www.aisnakeoil.com/feed"),
        ("The Gradient", "https://thegradient.pub/rss/"),
    ]
    posts = []
    for name, url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]:
                summary = entry.get("summary", "")
                posts.append({
                    "source": name,
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", "#"),
                    "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                })
        except Exception as e:
            print(f"RSS error for {name}: {e}")
    return posts[:12]


def build_html(arxiv, hf, blogs):
    today = datetime.now().strftime("%B %d, %Y")

    def section(items, renderer):
        return "".join(renderer(i) for i in items) if items else "<p style='color:#888;'>Nothing found today.</p>"

    def arxiv_item(p):
        return f"""
        <div class="item">
          <a href="{p['link']}">{p['title']}</a>
          <div class="meta">✍️ {p['authors']}</div>
          <p class="desc">{p['summary']}</p>
        </div>"""

    def hf_item(h):
        icon = "🧠" if h["type"] == "Model" else "🚀"
        return f"""
        <div class="item">
          <span class="badge">{h['type']}</span>
          <a href="{h['link']}">{icon} {h['name']}</a>
        </div>"""

    def blog_item(b):
        return f"""
        <div class="item">
          <span class="badge">{b['source']}</span>
          <a href="{b['link']}"> {b['title']}</a>
          <p class="desc">{b['summary']}</p>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#eef1f5;margin:0;padding:20px}}
  .wrap{{max-width:680px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,.12)}}

  /* Brand header */
  .header{{background:linear-gradient(135deg,#0a0a23 0%,#1a1a6e 60%,#2d2d9e 100%);color:#fff;padding:36px 30px 28px;text-align:center}}
  .brand-name{{font-size:22px;font-weight:800;letter-spacing:1px;margin:0 0 4px}}
  .brand-name span{{color:#7eb8f7}}
  .brand-tagline{{font-size:12px;opacity:.65;letter-spacing:2px;text-transform:uppercase;margin:0 0 18px}}
  .digest-title{{font-size:18px;font-weight:600;margin:0 0 6px;border-top:1px solid rgba(255,255,255,.2);padding-top:16px}}
  .digest-date{{font-size:13px;opacity:.75;margin:0}}

  /* Body */
  .body{{padding:28px 28px 10px}}
  .intro{{background:#f0f4ff;border-radius:8px;padding:14px 18px;margin-bottom:24px;font-size:13px;color:#444;line-height:1.6}}
  .intro strong{{color:#1a1a6e}}
  h2{{color:#0a0a23;border-bottom:2px solid #1a1a6e;padding-bottom:6px;margin-top:28px;font-size:15px;text-transform:uppercase;letter-spacing:.5px}}
  .item{{background:#f9faff;border-left:4px solid #1a1a6e;padding:12px 15px;margin:10px 0;border-radius:0 8px 8px 0}}
  .item a{{color:#1a1a6e;text-decoration:none;font-weight:700;font-size:14px}}
  .item a:hover{{text-decoration:underline;color:#2d2d9e}}
  .meta{{color:#888;font-size:12px;margin-top:4px}}
  .desc{{color:#555;font-size:13px;margin:6px 0 0;line-height:1.55}}
  .badge{{background:#1a1a6e;color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:700;margin-right:6px}}

  /* Footer */
  .footer{{background:#0a0a23;color:#aaa;font-size:12px;padding:22px;text-align:center;margin-top:20px}}
  .footer a{{color:#7eb8f7;text-decoration:none}}
  .footer .company{{color:#fff;font-weight:700;font-size:13px;margin-bottom:6px}}
  .divider{{border:none;border-top:1px solid #e8ecf5;margin:0}}
</style>
</head>
<body>
<div class="wrap">

  <div class="header">
    <div class="brand-name">Helias <span>AI</span> &amp; Analytics</div>
    <div class="brand-tagline">Intelligence · Insight · Innovation</div>
    <div class="digest-title">Agentic AI Daily Digest</div>
    <div class="digest-date">{today} &nbsp;·&nbsp; Papers &nbsp;·&nbsp; Demos &nbsp;·&nbsp; Blog Posts</div>
  </div>

  <div class="body">
    <div class="intro">
      Welcome to your daily briefing on <strong>Agentic AI</strong> — curated and delivered by
      <strong>Helias AI &amp; Analytics</strong>. Stay ahead of the latest research, tools, and
      industry news shaping autonomous AI systems.
    </div>

    <h2>📄 arXiv Research Papers</h2>
    {section(arxiv, arxiv_item)}

    <h2>🤗 Hugging Face Updates</h2>
    {section(hf, hf_item)}

    <h2>📰 Industry Blog Posts</h2>
    {section(blogs, blog_item)}
  </div>

  <hr class="divider">
  <div class="footer">
    <div class="company">Helias AI &amp; Analytics</div>
    This digest is produced and distributed by Helias AI &amp; Analytics.<br>
    Empowering businesses with cutting-edge AI research and insights.<br><br>
    <a href="mailto:hft4866@gmail.com">Contact Us</a> &nbsp;|&nbsp;
    <a href="https://github.com/henokfasil/Agentic_AI_News_Daily_Updates">GitHub</a><br><br>
    <span style="opacity:.5;font-size:11px">© {datetime.now().year} Helias AI &amp; Analytics. All rights reserved.</span>
  </div>

</div>
</body>
</html>"""


def send_email(subject, html_body):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise ValueError("GMAIL_USER and GMAIL_APP_PASSWORD must be set in .env")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ Email sent to {RECIPIENT_EMAIL}")


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting aggregation...")

    print("  → Fetching arXiv papers...")
    arxiv = fetch_arxiv_papers()
    print(f"     {len(arxiv)} papers")

    print("  → Fetching Hugging Face updates...")
    hf = fetch_huggingface_updates()
    print(f"     {len(hf)} items")

    print("  → Fetching blog RSS feeds...")
    blogs = fetch_blog_rss()
    print(f"     {len(blogs)} posts")

    today = datetime.now().strftime("%B %d, %Y")
    html = build_html(arxiv, hf, blogs)
    send_email(f"Helias AI & Analytics | Agentic AI Daily Digest — {today}", html)


if __name__ == "__main__":
    main()
