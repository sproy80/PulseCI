import asyncio
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import os

NEWS_FILE = "news_analysis.xlsx"

NEWS_COLUMNS = ["news_id", "datetime", "topic", "headline", "link", "summary", "source"]
TOPICS_COLUMNS = ["topic_id", "topic_name", "active_flag"]

RSS_FEEDS = {
    "markets": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "economy": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
}


async def fetch_feed(client: httpx.AsyncClient, url: str):
    """Fetch RSS feed XML text asynchronously."""
    try:
        resp = await client.get(url, timeout=10.0)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None


def parse_rss(xml_text: str, topic: str, source: str):
    """Parse RSS XML and return list of dicts with news entries."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    news_items = []
    for idx, item in enumerate(root.findall(".//item")):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        summary = item.findtext("description") or ""
        pub_date = item.findtext("pubDate") or ""

        # convert pubDate to datetime if possible
        try:
            dt = datetime.strptime(pub_date[:25], "%a, %d %b %Y %H:%M:%S")
        except Exception:
            dt = datetime.utcnow()

        news_items.append(
            {
                "news_id": f"{topic}_{idx}_{int(dt.timestamp())}",
                "datetime": dt,
                "topic": topic,
                "headline": title.strip(),
                "link": link.strip(),
                "summary": summary.strip(),
                "source": source,
            }
        )

    return news_items


async def collect_news():
    """Fetch and parse multiple RSS feeds asynchronously."""
    all_news = []

    async with httpx.AsyncClient() as client:
        tasks = [fetch_feed(client, url) for url in RSS_FEEDS.values()]
        results = await asyncio.gather(*tasks)

    for (topic, url), xml_text in zip(RSS_FEEDS.items(), results):
        if xml_text:
            news_items = parse_rss(xml_text, topic, url)
            all_news.extend(news_items)

    return all_news


def init_excel():
    """Create Excel file with empty sheets if not exists."""
    if not os.path.exists(NEWS_FILE):
        with pd.ExcelWriter(NEWS_FILE, engine="openpyxl") as writer:
            pd.DataFrame(columns=NEWS_COLUMNS).to_excel(writer, sheet_name="news", index=False)
            pd.DataFrame(columns=TOPICS_COLUMNS).to_excel(writer, sheet_name="news_topics", index=False)


async def save_news():
    init_excel()
    all_news = await collect_news()

    if not all_news:
        print("⚠️ No news fetched.")
        return

    # Load existing
    news_df = pd.read_excel(NEWS_FILE, sheet_name="news")

    # Append new
    new_df = pd.DataFrame(all_news)

    # Avoid duplicates based on news_id
    combined_df = pd.concat([news_df, new_df], ignore_index=True)
    combined_df.drop_duplicates(subset=["news_id"], inplace=True)

    # Save back
    with pd.ExcelWriter(NEWS_FILE, engine="openpyxl", mode="w") as writer:
        combined_df.to_excel(writer, sheet_name="news", index=False)

        # Keep topics sheet intact if present
        try:
            topics_df = pd.read_excel(NEWS_FILE, sheet_name="news_topics")
        except Exception:
            topics_df = pd.DataFrame(columns=TOPICS_COLUMNS)
        topics_df.to_excel(writer, sheet_name="news_topics", index=False)

    print(f"✅ Saved {len(new_df)} new entries. Total = {len(combined_df)}")


if __name__ == "__main__":
    asyncio.run(save_news())
