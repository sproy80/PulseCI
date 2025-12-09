from datetime import datetime, date, timedelta
import os
from typing import Dict, List
from fastapi import HTTPException
import feedparser
import pandas as pd
from dotenv import load_dotenv
import asyncio

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



async def get_all_topics() -> List[Dict]:
    df = await read_topics_sheet()
    df = df.where(pd.notnull(df), None)
    df = df.applymap(lambda x: x.item() if hasattr(x, "item") else x)
    # print(df)
    return df['topic_name'].values.tolist()


async def parse_google(topics:list, start_dt = "01-01-2023", end_dt="07-01-2025"):
    news_item = []

    start_dt = datetime.strptime(start_dt, "%m-%d-%Y")
    end_dt = datetime.strptime(end_dt, "%m-%d-%Y")

    for item in topics:
        feed = feedparser.parse(f"{news_url}{item.replace(' ', '+')}")

        for entry in feed.entries:
            published_raw = entry.published
            published_dt = datetime.strptime(published_raw, "%a, %d %b %Y %H:%M:%S %Z")
            published_str = published_dt.strftime("%m%d%Y")
            print(f"\rPublished Date : {published_str}", end="", flush=True)

            if start_dt <= published_dt <= end_dt:
                news_item.append(
                    {
                        "title" : entry.title,
                        "link" : entry.link,
                        "published" : published_str,
                        "summary" : entry.title_detail.value,

                    }

                )

    news_df = pd.DataFrame(news_item)
    news_df.to_csv("google_news.csv")
    return news_df



news_url = os.getenv("NEWS_URL")


if __name__ == "__main__":
    topics = asyncio.run(get_all_topics())

    today_date = date.today().strftime("%m-%d-%Y")
    one_month_ago_date = (date.today() - timedelta(days=30)).strftime("%m-%d-%Y")

    r = asyncio.run(parse_google(topics,start_dt=one_month_ago_date,end_dt=today_date))

    print("Completed")





