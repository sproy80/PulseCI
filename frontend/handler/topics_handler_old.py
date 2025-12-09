# topics_handler.py
import asyncio
import pandas as pd
import os
from fastapi import HTTPException
from typing import List, Dict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# EXCEL_FILE = os.path.join(BASE_DIR, "..", "news_analysis.xlsx")
EXCEL_FILE = r"C:\Projects\ml\PulseCI\news_analysis.xlsx"

SHEET_NAME = "news_topics"


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


# --- CRUD Methods ---
async def get_all_topics() -> List[Dict]:
    df = await read_topics_sheet()
    df = df.where(pd.notnull(df), None)
    df = df.applymap(lambda x: x.item() if hasattr(x, "item") else x)
    print(df)
    return df.to_dict(orient="records")


async def add_topic(topic_name: str) -> int:
    df = await read_topics_sheet()
    if df.empty:
        df = pd.DataFrame(columns=["topic_id", "topic_name", "active_flag"])

    # Check if topic exists (case-insensitive)
    if topic_name.lower() in df["topic_name"].str.lower().tolist():
        raise HTTPException(status_code=400, detail="Topic already exists.")

    next_id = int(df["topic_id"].max()) + 1 if not df.empty else 1
    new_topic = {"topic_id": next_id, "topic_name": topic_name, "active_flag": "Y"}
    df = pd.concat([df, pd.DataFrame([new_topic])], ignore_index=True)

    await save_topics_sheet(df)
    return next_id


async def update_topic_flag(topic_id: int, active_flag: str):
    df = await read_topics_sheet()

    if topic_id not in df["topic_id"].values:
        raise HTTPException(status_code=404, detail="Topic not found.")

    if active_flag.upper() not in ["Y", "N"]:
        raise HTTPException(status_code=400, detail="active_flag must be 'Y' or 'N'.")

    df.loc[df["topic_id"] == topic_id, "active_flag"] = active_flag.upper()
    await save_topics_sheet(df)


async def delete_topic(topic_id: int):
    # Soft delete by setting active_flag to 'N'
    df = await read_topics_sheet()

    if topic_id not in df["topic_id"].values:
        raise HTTPException(status_code=404, detail="Topic not found.")

    df.loc[df["topic_id"] == topic_id, "active_flag"] = "N"
    await save_topics_sheet(df)


if __name__ == "__main__":
    # asyncio.run(add_topic(topic_name='test14'))
    # asyncio.run(update_topic_flag(topic_id=14,active_flag='N'))
    asyncio.run(delete_topic(topic_id=10))
    asyncio.run(get_all_topics())