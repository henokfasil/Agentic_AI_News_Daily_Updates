import os
import smtplib
import requests
import urllib.parse
import json
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import feedparser
import hashlib

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", GMAIL_USER)

# Deduplication cache
CACHE_FILE = "sent_items.json"
DEDUP_DAYS = 7  # Don't resend items from the past 7 days


# ---------------------------------------------------------------------------
# Cache management for deduplication
# ---------------------------------------------------------------------------
def hash_item(item_data):
    """Generate a hash for an item to track if it's been sent before."""
    item_str = json.dumps(item_data, sort_keys=True)
    return hashlib.md5(item_str.encode()).hexdigest()

def load_cache():
    """Load the cache of previously sent items."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_cache(cache):
    """Save the cache of sent items."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def is_item_new(item_hash, cache):
    """Check if an item is new (not sent in the past DEDUP_DAYS days)."""
    if item_hash not in cache:
        return True
    sent_date = datetime.fromisoformat(cache[item_hash])
    days_ago = (datetime.now() - sent_date).days
    return days_ago >= DEDUP_DAYS

def filter_new_items(items, key_fields, cache):
    """Filter items list to only include new ones not sent recently."""
    new_items = []
    for item in items:
        # Create hashable dict from specified fields
        hash_data = {k: item.get(k) for k in key_fields if k in item}
        item_hash = hash_item(hash_data)
        if is_item_new(item_hash, cache):
            new_items.append((item, item_hash))
    return new_items

# ---------------------------------------------------------------------------
# 1. Hugging Face — trending models & spaces (agentic AI search)
# ---------------------------------------------------------------------------
def fetch_huggingface_trending():
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
                    base = "spaces/" if kind == "Space" else ""
                    results.append({
                        "type": kind,
                        "name": item_id,
                        "link": f"https://huggingface.co/{base}{item_id}",
                    })
        except Exception as e:
            print(f"  HF {kind} error: {e}")
    return results


# ---------------------------------------------------------------------------
# 2. New model releases — watch key labs on Hugging Face
# ---------------------------------------------------------------------------
def fetch_new_model_releases():
    orgs = [
        ("moonshotai",   "Kimi / Moonshot AI"),
        ("THUDM",        "GLM / Zhipu AI"),
        ("Qwen",         "Qwen / Alibaba"),
        ("deepseek-ai",  "DeepSeek"),
        ("meta-llama",   "Meta Llama"),
        ("mistralai",    "Mistral AI"),
        ("google",       "Google"),
        ("microsoft",    "Microsoft"),
        ("01-ai",        "Yi / 01.AI"),
        ("cohere-for-ai","Cohere"),
        ("xai-org",      "xAI / Grok"),
    ]
    releases = []
    for org_id, org_label in orgs:
        try:
            url = f"https://huggingface.co/api/models?author={org_id}&sort=lastModified&direction=-1&limit=3"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                items = r.json()
                for item in items[:2]:
                    item_id = item.get("modelId", "")
                    releases.append({
                        "org": org_label,
                        "name": item_id,
                        "link": f"https://huggingface.co/{item_id}",
                    })
        except Exception as e:
            print(f"  HF org error [{org_label}]: {e}")
    return releases


# ---------------------------------------------------------------------------
# 3. Framework & tool releases — GitHub Atom feeds
# ---------------------------------------------------------------------------
def fetch_github_releases():
    repos = [
        ("VS Code",            "microsoft/vscode"),
        ("AutoGen",            "microsoft/autogen"),
        ("Semantic Kernel",    "microsoft/semantic-kernel"),
        ("CrewAI",             "crewAIInc/crewAI"),
        ("LangGraph",          "langchain-ai/langgraph"),
        ("LlamaIndex",         "run-llama/llama_index"),
        ("PydanticAI",         "pydantic/pydantic-ai"),
        ("OpenAI Agents SDK",  "openai/openai-agents-python"),
        ("Dify",               "langgenius/dify"),
        ("Agno",               "agno-agi/agno"),
        ("LiteLLM",            "BerriAI/litellm"),
        ("Mem0",               "mem0ai/mem0"),
        ("n8n",                "n8n-io/n8n"),
        ("Flowise",            "FlowiseAI/Flowise"),
    ]
    releases = []
    for name, repo in repos:
        try:
            feed = feedparser.parse(f"https://github.com/{repo}/releases.atom")
            if feed.entries:
                e = feed.entries[0]
                releases.append({
                    "name": name,
                    "repo": repo,
                    "version": e.title,
                    "link": e.link,
                    "updated": e.get("updated", "")[:10],
                })
        except Exception as ex:
            print(f"  GitHub releases error [{name}]: {ex}")
    return releases


# ---------------------------------------------------------------------------
# 4. Industry news & blog posts — expanded RSS list
# ---------------------------------------------------------------------------
def fetch_blog_rss():
    feeds = [
        # AI Labs
        ("Anthropic",        "https://www.anthropic.com/feed.xml"),
        ("OpenAI",           "https://openai.com/blog/rss.xml"),
        ("Google DeepMind",  "https://deepmind.google/blog/rss.xml"),
        ("Meta AI",          "https://ai.meta.com/blog/rss/"),
        ("Microsoft AI",     "https://blogs.microsoft.com/ai/feed/"),
        ("Mistral AI",       "https://mistral.ai/fr/news/rss.xml"),
        ("xAI",              "https://x.ai/blog/rss.xml"),
        ("NVIDIA",           "https://blogs.nvidia.com/feed/"),
        # Open-source / HF ecosystem
        ("Hugging Face",     "https://huggingface.co/blog/feed.xml"),
        ("LangChain",        "https://blog.langchain.dev/rss/"),
        # Dev tools
        ("VS Code",          "https://code.visualstudio.com/feed.xml"),
        ("GitHub",           "https://github.blog/feed/"),
        ("GitHub Changelog", "https://github.blog/changelog/feed/"),
        # Industry news
        ("VentureBeat AI",   "https://venturebeat.com/category/ai/feed/"),
        ("TechCrunch AI",    "https://techcrunch.com/category/artificial-intelligence/feed/"),
        ("MIT Tech Review",  "https://www.technologyreview.com/feed/"),
        ("Wired AI",         "https://www.wired.com/feed/category/artificial-intelligence/latest/rss"),
        # Research & commentary
        ("The Gradient",     "https://thegradient.pub/rss/"),
        ("Import AI",        "https://jack-clark.net/feed/"),
        ("AI Snake Oil",     "https://www.aisnakeoil.com/feed"),
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
                    "link":  entry.get("link", "#"),
                    "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                })
        except Exception as e:
            print(f"  RSS error [{name}]: {e}")
    return posts[:20]


# ---------------------------------------------------------------------------
# 5. arXiv research papers
# ---------------------------------------------------------------------------
def fetch_arxiv_papers():
    query = urllib.parse.quote(
        "agentic AI OR AI agent OR autonomous agent OR multi-agent LLM OR agentic workflow"
    )
    url = (
        "http://export.arxiv.org/api/query"
        f"?search_query=all:{query}&start=0&max_results=10"
        "&sortBy=lastUpdatedDate&sortOrder=descending"
    )
    feed = feedparser.parse(url)
    papers = []
    for entry in feed.entries[:8]:
        authors = ", ".join(a.name for a in entry.get("authors", [])[:3]) or "Unknown"
        summary = entry.get("summary", "")
        papers.append({
            "title":   entry.title.replace("\n", " "),
            "summary": summary[:300] + "..." if len(summary) > 300 else summary,
            "link":    entry.link,
            "authors": authors,
        })
    return papers


# ---------------------------------------------------------------------------
# HTML email builder
# ---------------------------------------------------------------------------
def build_html(hf_trending, model_releases, gh_releases, blogs, arxiv):
    today = datetime.now().strftime("%B %d, %Y")

    def section_or_empty(items, renderer):
        return "".join(renderer(i) for i in items) if items else \
               "<p style='color:#888;padding:10px 0;'>Nothing new found today.</p>"

    # --- renderers ---
    def hf_item(h):
        icon = "🧠" if h["type"] == "Model" else "🚀"
        return f"""
        <div class="item">
          <span class="badge">{h['type']}</span>
          <a href="{h['link']}">{icon} {h['name']}</a>
        </div>"""

    def release_item(r):
        return f"""
        <div class="item">
          <span class="badge">{r['org']}</span>
          <a href="{r['link']}">🆕 {r['name']}</a>
        </div>"""

    def gh_item(g):
        date = f" <span style='color:#aaa;font-size:11px;'>({g['updated']})</span>" if g["updated"] else ""
        return f"""
        <div class="item">
          <span class="badge gh">Release</span>
          <a href="{g['link']}">⚙️ {g['name']} — {g['version']}</a>{date}
        </div>"""

    def blog_item(b):
        return f"""
        <div class="item">
          <span class="badge">{b['source']}</span>
          <a href="{b['link']}"> {b['title']}</a>
          <p class="desc">{b['summary']}</p>
        </div>"""

    def arxiv_item(p):
        return f"""
        <div class="item">
          <a href="{p['link']}">{p['title']}</a>
          <div class="meta">✍️ {p['authors']}</div>
          <p class="desc">{p['summary']}</p>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#eef1f5;margin:0;padding:20px}}
  .wrap{{max-width:700px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,.12)}}

  .header{{background:linear-gradient(135deg,#0a0a23 0%,#1a1a6e 60%,#2d2d9e 100%);color:#fff;padding:36px 30px 28px;text-align:center}}
  .brand-name{{font-size:22px;font-weight:800;letter-spacing:1px;margin:0 0 4px}}
  .brand-name span{{color:#7eb8f7}}
  .brand-tagline{{font-size:12px;opacity:.65;letter-spacing:2px;text-transform:uppercase;margin:0 0 18px}}
  .digest-title{{font-size:18px;font-weight:600;margin:0 0 6px;border-top:1px solid rgba(255,255,255,.2);padding-top:16px}}
  .digest-date{{font-size:13px;opacity:.75;margin:0}}

  .body{{padding:28px 28px 10px}}
  .intro{{background:#f0f4ff;border-radius:8px;padding:14px 18px;margin-bottom:10px;font-size:13px;color:#444;line-height:1.6}}
  .intro strong{{color:#1a1a6e}}
  h2{{color:#0a0a23;border-bottom:2px solid #1a1a6e;padding-bottom:6px;margin-top:30px;font-size:14px;text-transform:uppercase;letter-spacing:.6px}}
  .item{{background:#f9faff;border-left:4px solid #1a1a6e;padding:11px 14px;margin:8px 0;border-radius:0 8px 8px 0}}
  .item a{{color:#1a1a6e;text-decoration:none;font-weight:700;font-size:13px}}
  .item a:hover{{text-decoration:underline;color:#2d2d9e}}
  .meta{{color:#888;font-size:11px;margin-top:4px}}
  .desc{{color:#555;font-size:12px;margin:5px 0 0;line-height:1.5}}
  .badge{{background:#1a1a6e;color:#fff;padding:2px 7px;border-radius:3px;font-size:10px;font-weight:700;margin-right:5px}}
  .badge.gh{{background:#238636}}

  .footer{{background:#0a0a23;color:#aaa;font-size:12px;padding:22px;text-align:center;margin-top:20px}}
  .footer a{{color:#7eb8f7;text-decoration:none}}
  .footer .company{{color:#fff;font-weight:700;font-size:13px;margin-bottom:6px}}
  hr{{border:none;border-top:1px solid #e8ecf5;margin:0}}
</style>
</head>
<body>
<div class="wrap">

  <div class="header">
    <div class="brand-name">Helias <span>AI</span> &amp; Analytics</div>
    <div class="brand-tagline">Intelligence · Insight · Innovation</div>
    <div class="digest-title">Agentic AI Daily Digest</div>
    <div class="digest-date">{today} &nbsp;·&nbsp; Models · Releases · News · Research</div>
  </div>

  <div class="body">

    <h2>🤗 Hugging Face — Trending Models &amp; Spaces</h2>
    {section_or_empty(hf_trending, hf_item)}

    <h2>🆕 New Model Releases (Kimi · GLM · Qwen · Llama · Mistral &amp; more)</h2>
    {section_or_empty(model_releases, release_item)}

    <h2>⚙️ Framework &amp; Tool Releases (VS Code · AutoGen · CrewAI · LangGraph &amp; more)</h2>
    {section_or_empty(gh_releases, gh_item)}

    <h2>📰 Industry News &amp; Blog Posts</h2>
    {section_or_empty(blogs, blog_item)}

    <h2>📄 arXiv Research Papers</h2>
    {section_or_empty(arxiv, arxiv_item)}

    <div class="intro" style="margin-top:28px;">
      <strong>About this digest:</strong> Your daily briefing on <strong>Agentic AI</strong> —
      curated and delivered by <strong>Helias AI &amp; Analytics</strong>. Covering model releases
      from every major lab, open-source framework updates, VS Code &amp; dev tool releases,
      industry news, and the latest academic research on autonomous AI systems.
    </div>

  </div>

  <hr>
  <div class="footer">
    <div class="company">Helias AI &amp; Analytics</div>
    Empowering businesses with cutting-edge AI research and insights.<br><br>
    <a href="mailto:hft4866@gmail.com">Contact Us</a> &nbsp;|&nbsp;
    <a href="https://github.com/henokfasil/Agentic_AI_News_Daily_Updates">GitHub</a><br><br>
    <span style="opacity:.5;font-size:11px">© {datetime.now().year} Helias AI &amp; Analytics. All rights reserved.</span>
  </div>

</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Email sender
# ---------------------------------------------------------------------------
def send_email(subject, html_body):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise ValueError("GMAIL_USER and GMAIL_APP_PASSWORD must be set in .env")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ Email sent to {RECIPIENT_EMAIL}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    start_time = datetime.now()
    print(f"\n[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] Starting aggregation...")
    print(f"  📧 Deduplication: tracking sent items from past {DEDUP_DAYS} days")

    # Load cache
    cache = load_cache()
    items_sent_before = len(cache)
    print(f"  📦 Cache loaded: {items_sent_before} items previously sent")

    print("  → Hugging Face trending...")
    hf_trending_raw = fetch_huggingface_trending()
    hf_trending_filtered = [item for item, _ in filter_new_items(hf_trending_raw, ['name', 'type'], cache)]
    print(f"     {len(hf_trending_raw)} total, {len(hf_trending_filtered)} new")

    print("  → New model releases (HF orgs)...")
    model_releases_raw = fetch_new_model_releases()
    model_releases_filtered = [item for item, _ in filter_new_items(model_releases_raw, ['name', 'org'], cache)]
    print(f"     {len(model_releases_raw)} total, {len(model_releases_filtered)} new")

    print("  → GitHub framework/tool releases...")
    gh_releases_raw = fetch_github_releases()
    gh_releases_filtered = [item for item, _ in filter_new_items(gh_releases_raw, ['name', 'version'], cache)]
    print(f"     {len(gh_releases_raw)} total, {len(gh_releases_filtered)} new")

    print("  → Industry blogs & news...")
    blogs_raw = fetch_blog_rss()
    blogs_filtered = [item for item, _ in filter_new_items(blogs_raw, ['title', 'source'], cache)]
    print(f"     {len(blogs_raw)} total, {len(blogs_filtered)} new")

    print("  → arXiv papers...")
    arxiv_raw = fetch_arxiv_papers()
    arxiv_filtered = [item for item, _ in filter_new_items(arxiv_raw, ['title', 'authors'], cache)]
    print(f"     {len(arxiv_raw)} total, {len(arxiv_filtered)} new")

    # Only send if there are new items
    if not any([hf_trending_filtered, model_releases_filtered, gh_releases_filtered, blogs_filtered, arxiv_filtered]):
        print(f"  ⏭️  No new items found. Skipping email.")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aggregation complete (no changes)")
        return

    today = datetime.now().strftime("%B %d, %Y")
    html = build_html(hf_trending_filtered, model_releases_filtered, gh_releases_filtered, blogs_filtered, arxiv_filtered)
    send_email(f"Helias AI & Analytics | Agentic AI Daily Digest — {today}", html)

    # Update cache with newly sent items
    for items, key_fields in [
        (hf_trending_raw, ['name', 'type']),
        (model_releases_raw, ['name', 'org']),
        (gh_releases_raw, ['name', 'version']),
        (blogs_raw, ['title', 'source']),
        (arxiv_raw, ['title', 'authors']),
    ]:
        for item in items:
            hash_data = {k: item.get(k) for k in key_fields if k in item}
            item_hash = hash_item(hash_data)
            cache[item_hash] = datetime.now().isoformat()

    save_cache(cache)
    print(f"  💾 Cache updated: {len(cache) - items_sent_before} new items tracked")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aggregation complete ✅")


if __name__ == "__main__":
    main()
