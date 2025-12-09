# backend/app/main.py
from fastapi import FastAPI
from .utils.config import settings
from .utils.logger import get_logger
from .routers import news
from .routers.topics import router as topics_router

logger = get_logger()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

app.include_router(topics_router, prefix="/topics", tags=["Topics"])

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

# Dummy news endpoint for now
@app.get("/api/news")
async def get_news():
    return {"message": "News API working"}

# Register Routers
app.include_router(news.router)
