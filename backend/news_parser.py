#news_parser.py
from datetime import datetime, date, timedelta
import os
from typing import Dict, List
from fastapi import HTTPException
import feedparser
import pandas as pd
from dotenv import load_dotenv
import asyncio
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()

load_dotenv()
EXCEL_FILE = r"C:\Projects\ml\PulseCI\news_analysis.xlsx"

SHEET_NAME = "news_topics"

news_url = os.getenv("NEWS_URL")


# --- Helper functions for Excel ---
async def read_topics_sheet() -> pd.DataFrame:
    if not os.path.exists(EXCEL_FILE):
        raise HTTPException(status_code=500, detail="Excel database not found.")

    df = await asyncio.to_thread(pd.read_excel, EXCEL_FILE, sheet_name=SHEET_NAME)
    return df

async def save_topics_sheet(df: pd.DataFrame):
    def _write():
        with pd.ExcelWriter(EXCEL_FILE, mode="w", engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
    await asyncio.to_thread(_write)


NEWS_SHEET = "news"

# Read the news sheet
async def read_news_sheet() -> pd.DataFrame:
    if not os.path.exists(EXCEL_FILE):
        raise HTTPException(status_code=500, detail="Excel database not found.")

    df = await asyncio.to_thread(pd.read_excel, EXCEL_FILE, sheet_name=NEWS_SHEET)
    return df


# Save news sheet back to Excel without damaging other sheets
async def save_news_sheet(df: pd.DataFrame):
    # Load full workbook and replace only the "news" sheet
    def _write():
        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=NEWS_SHEET, index=False)

    await asyncio.to_thread(_write)




async def get_all_topics() -> List[Dict]:
    df = await read_topics_sheet()
    df = df.where(pd.notnull(df), None)
    # df = df.applymap(lambda x: x.item() if hasattr(x, "item") else x)
    df = df.apply(lambda col: col.map(lambda x: x.item() if hasattr(x, "item") else x))

    # print(df)
    return df['topic_name'].values.tolist()

def categorize_news(text: str) -> str:
    text_lower = text.lower()

    categories = {
        "acquisition": ["acquire", "acquisition", "buy", "merger", "takeover"],
        "partnership": ["partner", "partnership", "collaborate", "alliance"],
        "product_launch": ["launch", "release", "introduce", "unveiled", "new product"],
        "financial": ["profit", "loss", "revenue", "earnings", "financial"],
        "leadership_change": ["ceo", "appoint", "chief", "executive", "leadership"],
        "technology": ["ai", "machine learning", "cloud", "platform", "technology"],
    }

    for category, keywords in categories.items():
        if any(k in text_lower for k in keywords):
            return category

    return "other"



async def parse_google(topics: list, start_dt="01-01-2023", end_dt="07-01-2025"):
    news_item = []
    start_dt = datetime.strptime(start_dt, "%m-%d-%Y")
    end_dt = datetime.strptime(end_dt, "%m-%d-%Y")

    for item in topics:
        feed = feedparser.parse(f"{news_url}{item.replace(' ', '+')}")
        for entry in feed.entries:
            published_raw = entry.published
            published_dt = datetime.strptime(published_raw, "%a, %d %b %Y %H:%M:%S %Z")
            published_str = published_dt.strftime("%m%d%Y")

            if start_dt <= published_dt <= end_dt:
                score = analyzer.polarity_scores(entry.title)['compound']

                if score > 0.2:
                    sentiment_label = "Positive"
                elif score < -0.2:
                    sentiment_label = "Negative"
                else:
                    sentiment_label = "Neutral"


                category = categorize_news(entry.title)

                news_item.append(
                    {
                        "title": entry.title,
                        "link": entry.link,
                        "published": published_str,
                        "summary": entry.title_detail.value,
                        "source" : entry.source["title"],
                        "sentiment": sentiment_label,
                        "sentiment_score" : score,
                        "topic": item,
                        "category" : category
                    }
                )

    # Convert to DataFrame
    new_df = pd.DataFrame(news_item)

    # Read existing sheet
    try:
        old_df = await read_news_sheet()
    except:
        old_df = pd.DataFrame(columns=["news_id", "title", "link", "published", "summary","source","sentiment"])



    # Remove duplicates based on link
    combined_df = pd.concat([old_df, new_df], ignore_index=True)
    combined_df.drop_duplicates(subset=["link"], keep="first", inplace=True)

    # Remove old news_id if exists
    if "news_id" in combined_df.columns:
        combined_df.drop(columns=["news_id"], inplace=True)

    # Auto-increment news_id
    combined_df = combined_df.reset_index(drop=True)
    combined_df.insert(0, "news_id", combined_df.index + 1)

    # Save back to Excel
    await save_news_sheet(combined_df)


    # # Remove duplicates based on link
    # combined_df = pd.concat([old_df, new_df], ignore_index=True)
    # combined_df.drop_duplicates(subset=["link"], keep="first", inplace=True)

    # # Auto-increment news_id
    # combined_df = combined_df.reset_index(drop=True)
    # combined_df.insert(0, "news_id", combined_df.index + 1)

    # # Save back to Excel
    # await save_news_sheet(combined_df)

    return combined_df



news_url = os.getenv("NEWS_URL")


if __name__ == "__main__":
    topics = asyncio.run(get_all_topics())

    today_date = date.today().strftime("%m-%d-%Y")
    one_month_ago_date = (date.today() - timedelta(days=30)).strftime("%m-%d-%Y")

    r = asyncio.run(parse_google(topics,start_dt=one_month_ago_date,end_dt=today_date))

    print("Completed")





