# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "PulseCI"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/pulseci")
    EXCEL_PATH: str = os.getenv("EXCEL_PATH", "data/news.xlsx")


settings = Settings()
