# backend/app/main.py
from fastapi import FastAPI
from app.config import settings
from app.utils.logger import get_logger
from app.database import init_db
from app.routers import news

logger = get_logger()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)


@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Application startup complete.")


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

app.include_router(news.router)
