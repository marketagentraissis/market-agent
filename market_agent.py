import anthropic
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import schedule
import time
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

client = anthropic.Anthropic()

# ── Email Configuration ────────────────────────────────────────────────────────
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = "marketagentraissis@gmail.com"      # The Gmail you just created
TO_EMAIL = "sraissis@opengatecapital.com" # Where you want to receive the briefing

# ── News Sources ───────────────────────────────────────────────────────────────
RSS_FEEDS = [
    # Reuters
    "https://feeds.reuters.com/reuters/businessNews",
    "https://feeds.reuters.com/reuters/europeanFinancialNews",
    "https://feeds.reuters.com/reuters/mergersNews",
    "https://feeds.reuters.com/reuters/economy",
    # Wall Street Journal
    "https://feeds.wsj.com/wsj/xml/rss/3_7085.xml",
    # CNBC
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    # Financial Times
    "https://www.ft.com/rss/home/uk",
    # MarketWatch
    "https://feeds.marketwatch.com/marketwatch/topstories",
    "https://feeds.marketwatch.com/marketwatch/marketpulse",
    # Seeking Alpha
    "https://seekingalpha.com/market_currents.xml",
    # Investing.com
    "https://www.investing.com/rss/news.rss",
    # Bloomberg
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.bloomberg.com/politics/news.rss",
    # The Economist
    "https://www.economist.com/finance-and-economics/rss.xml",
    "https://www.economist.com/business/rss.xml",
    # Fortune
    "https://fortune.com/feed/fortune-feeds/?id=3230629",
    # Barron's
    "https://www.barrons.com/xml/rss/3_7510.xml",
    # Harvard Business Review
    "https://hbr.org/topics/finance/rss",
]

def fetch_articles(feeds, max_per_feed=5):
    articles = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_per_feed]:
            article = {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", ""),
            }
            articles.append(article)
    return articles

def generate_briefing(articles):
    articles_text = ""
    for i, a in enumerate(articles, 1):
        articles_text += f"""
Article {i}: {a['title']}
Published: {a.get('published', 'N/A')}
Content: {a.get('summary', 'No content available')}
---"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": f"""You are a senior market analyst preparing a morning briefing for a Private Equity professional.

Today is {datetime.now().strftime('%A, %B %d, %Y')}.

Below are {len(articles)} articles from major financial news sources gathered this morning.

{articles_text}

Please provide a structured morning market briefing covering:

1. US Market Overview - Key pre-market moves, macro drivers, Fed/economic data
2. European Market Overview - Key moves in FTSE, DAX, CAC, macro drivers
3. Top 3-5 Stories to Watch - Most impactful news items for PE/deal activity
4. Sector Highlights - Any sectors with notable moves or news
5. Key Risks Today - Anything that could create volatility or affect deal markets

Be concise, specific, and analytical. Use numbers where available. Format for easy skimming."""
            }
        ]
    )
    return response.content[0].text

def send_email(briefing):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAIL,
        subject=f"Morning Market Briefing — {datetime.now().strftime('%B %d, %Y')}",
        plain_text_content=briefing
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent successfully! Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")

def run_morning_briefing():
    print(f"\n{'='*60}")
    print(f"  Morning Market Briefing — {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
    print(f"{'='*60}\n")

    print("Fetching articles...")
    articles = fetch_articles(RSS_FEEDS, max_per_feed=4)
    print(f"Fetched {len(articles)} articles. Generating briefing...\n")

    briefing = generate_briefing(articles)
    print(briefing)

    # Save to file
    filename = f"briefing_{datetime.now().strftime('%Y-%m-%d')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(briefing)
    print(f"\n[Saved to {filename}]")

    # Send email
    print("Sending email...")
    send_email(briefing)

schedule.every().day.at("08:00").do(run_morning_briefing)

if __name__ == "__main__":
    print("Market briefing agent started.")
    run_morning_briefing()
    while True:
        schedule.run_pending()
        time.sleep(60)