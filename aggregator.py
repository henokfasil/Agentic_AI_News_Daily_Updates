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
  body{{font-family:Arial,sans-serif;background:#f0f2f5;margin:0;padding:20px}}
  .wrap{{max-width:680px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1)}}
  .header{{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:30px;text-align:center}}
  .header h1{{margin:0;font-size:24px}}
  .header p{{margin:8px 0 0;opacity:.8;font-size:14px}}
  .body{{padding:25px}}
  h2{{color:#1a1a2e;border-bottom:2px solid #4CAF50;padding-bottom:6px;margin-top:28px}}
  .item{{background:#f9f9f9;border-left:4px solid #4CAF50;padding:12px 15px;margin:10px 0;border-radius:0 6px 6px 0}}
  .item a{{color:#0066cc;text-decoration:none;font-weight:600;font-size:14px}}
  .item a:hover{{text-decoration:underline}}
  .meta{{color:#888;font-size:12px;margin-top:4px}}
  .desc{{color:#444;font-size:13px;margin:6px 0 0;line-height:1.5}}
  .badge{{background:#4CAF50;color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600;margin-right:6px}}
  .footer{{text-align:center;color:#aaa;font-size:12px;padding:20px;border-top:1px solid #eee;background:#fafafa}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>🤖 Agentic AI Daily Digest</h1>
    <p>{today} — Papers · Demos · Blog Posts</p>
  </div>
  <div class="body">
    <h2>📄 arXiv Papers</h2>
    {section(arxiv, arxiv_item)}

    <h2>🤗 Hugging Face Updates</h2>
    {section(hf, hf_item)}

    <h2>📰 Blog Posts</h2>
    {section(blogs, blog_item)}
  </div>
  <div class="footer">
    🤖 Agentic AI News Bot — runs daily at 7 AM UTC<br>
    <a href="https://github.com/henokfasil/Agentic_AI_News_Daily_Updates" style="color:#0066cc;">View on GitHub</a>
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
    send_email(f"🤖 Agentic AI Daily Digest — {today}", html)


if __name__ == "__main__":
    main()
