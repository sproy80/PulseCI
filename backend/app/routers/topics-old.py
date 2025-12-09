import pandas as pd
from fastapi import APIRouter, HTTPException
import os
import asyncio
import json

router = APIRouter(prefix="/api/topics", tags=["Topics"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, "..", "news_analysis.xlsx")


EXCEL_FILE = r"C:\Projects\ml\PulseCI\news_analysis.xlsx"
SHEET_NAME = "news_topics"


async def read_topics_sheet():
    if not os.path.exists(EXCEL_FILE):
        raise HTTPException(status_code=500, detail="Excel database not found.")
    
    return pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)


async def save_topics_sheet(df: pd.DataFrame):
    with pd.ExcelWriter(EXCEL_FILE, mode="w", if_sheet_exists="overlay", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=SHEET_NAME, index=False)


# GET all topics
@router.get("/")
async def get_topics():
    df = await read_topics_sheet()

    # Convert numpy types → Python native types
    df = df.where(pd.notnull(df), None)  
    df = df.applymap(lambda x: x.item() if hasattr(x, "item") else x)

    return df.to_dict(orient="records")
    


#Add new topic
@router.post("/")
async def add_topic(topic_name: str):
    df = await read_topics_sheet()

    if df.empty:
        print("No data found")

    # Convert existing topic names to lowercase for comparison
    if topic_name.lower() in df["topic_name"].str.lower().values:
        raise HTTPException(status_code=400, detail="Topic already exists.")

    # Auto increment topic_id
    next_id = df["topic_id"].max() + 1 if not df.empty else 1

    new_topic = {
        "topic_id": next_id,
        "topic_name": topic_name,
        "active_flag": "Y"
    }

    df = pd.concat([df, pd.DataFrame([new_topic])], ignore_index=True)

    # await asyncio.to_thread(save_topics_sheet, df)
    await save_topics_sheet(df)

    return {"message": "Topic added successfully", "topic_id": next_id}

# UPDATE topic name
@router.put("/{topic_id}")
async def update_topic(topic_id: int, active_flag: str):
    df = await read_topics_sheet()

    if topic_id not in df["topic_id"].values:
        raise HTTPException(status_code=404, detail="Topic not found.")

    if active_flag.upper() not in ["Y", "N"]:
        raise HTTPException(status_code=400, detail="active_flag must be 'Y' or 'N'.")

    df.loc[df["topic_id"] == topic_id, "active_flag"] = active_flag.upper()

    await asyncio.to_thread(save_topics_sheet, df)

    return {"message": "Topic active flag updated successfully"}



# DELETE topic (soft delete)
@router.delete("/{topic_id}")
async def delete_topic(topic_id: int):
    df = await read_topics_sheet()

    if topic_id not in df["topic_id"].values:
        raise HTTPException(status_code=404, detail="Topic not found.")

    df.loc[df["topic_id"] == topic_id, "active_flag"] = "N"

    await asyncio.to_thread(save_topics_sheet, df)

    return {"message": "Topic deactivated successfully"}


if __name__ == "__main__":
    asyncio.run(read_topics_sheet())