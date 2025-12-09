# backend/app/routers/news.py
from fastapi import APIRouter
from ..database import load_excel_data

router = APIRouter(prefix="/news", tags=["News"])


@router.get("/")
async def get_news():
    df = load_excel_data()
    return {"total_records": len(df), "data_sample": df.head(5).to_dict(orient="records")}
