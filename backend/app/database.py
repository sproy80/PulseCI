# backend/app/database.py
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()

engine = None


async def init_db():
    global engine
    try:
        engine = create_async_engine(
            settings.DATABASE_URL, echo=False, future=True)
        logger.info("PostgreSQL connection initialized.")
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")


def load_excel_data():
    try:
        df = pd.read_excel(settings.EXCEL_PATH)
        logger.info(f"Excel data loaded from {settings.EXCEL_PATH}")
        return df
    except FileNotFoundError:
        logger.error(f"Excel file not found: {settings.EXCEL_PATH}")
        return pd.DataFrame()
