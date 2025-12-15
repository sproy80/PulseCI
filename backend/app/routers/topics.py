# topics.py
import os
import asyncio
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/topics", tags=["Topics"])

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# EXCEL_FILE = os.path.join(BASE_DIR, "..", "news_analysis.xlsx")
EXCEL_FILE = r"C:\Projects\ml\PulseCI\news_analysis.xlsx"
SHEET_NAME = "news_topics"

# --- Pydantic Models ---
class TopicCreate(BaseModel):
    topic_name: str

class TopicUpdate(BaseModel):
    active_flag: str  # 'Y' or 'N'

# --- Helper Functions ---
async def read_topics_sheet() -> pd.DataFrame:
    if not os.path.exists(EXCEL_FILE):
        raise HTTPException(status_code=500, detail="Excel database not found.")

    # Run blocking IO in thread
    df = await asyncio.to_thread(pd.read_excel, EXCEL_FILE, sheet_name=SHEET_NAME)
    return df

async def save_topics_sheet(df: pd.DataFrame):
    def _write():
        with pd.ExcelWriter(
            EXCEL_FILE,
            mode="a",
            if_sheet_exists="replace",
            engine="openpyxl"
        ) as writer:
            df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

    await asyncio.to_thread(_write)


# --- Routes ---
         
# GET all topics
@router.get("/")
async def get_topics():
    df = await read_topics_sheet()
    df = df.where(pd.notnull(df), None)
    df = df.applymap(lambda x: x.item() if hasattr(x, "item") else x)
    return df.to_dict(orient="records")

# POST add new topic
@router.post("/")
async def add_topic(topic: TopicCreate):
    df = await read_topics_sheet()

    if df.empty:
        df = pd.DataFrame(columns=["topic_id", "topic_name", "active_flag"])

    # Case-insensitive check
    if topic.topic_name.lower() in df["topic_name"].str.lower().tolist():
        raise HTTPException(status_code=400, detail="Topic already exists.")

    # Auto increment topic_id
    next_id = int(df["topic_id"].max()) + 1 if not df.empty else 1

    new_topic = {"topic_id": next_id, "topic_name": topic.topic_name, "active_flag": "Y"}
    df = pd.concat([df, pd.DataFrame([new_topic])], ignore_index=True)

    await save_topics_sheet(df)
    return {"message": "Topic added successfully", "topic_id": next_id}

# PUT update topic
@router.put("/{topic_id}")
async def update_topic(topic_id: int, update: TopicUpdate):
    df = await read_topics_sheet()

    if topic_id not in df["topic_id"].values:
        raise HTTPException(status_code=404, detail="Topic not found.")

    if update.active_flag.upper() not in ["Y", "N"]:
        raise HTTPException(status_code=400, detail="active_flag must be 'Y' or 'N'.")

    df.loc[df["topic_id"] == topic_id, "active_flag"] = update.active_flag.upper()
    await save_topics_sheet(df)
    return {"message": "Topic active flag updated successfully"}

# DELETE (soft delete)
@router.delete("/{topic_id}")
async def delete_topic(topic_id: int):
    df = await read_topics_sheet()

    if topic_id not in df["topic_id"].values:
        raise HTTPException(status_code=404, detail="Topic not found.")

    df.loc[df["topic_id"] == topic_id, "active_flag"] = "N"
    await save_topics_sheet(df)
    return {"message": "Topic deactivated successfully"}
