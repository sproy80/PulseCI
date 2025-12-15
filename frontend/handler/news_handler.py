# news_handler.py
import asyncio
import httpx
from typing import List, Dict

# Base URL of your FastAPI server
BASE_URL = "http://localhost:8000/api/news"


# GET all news
async def get_all_news() -> List[Dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(BASE_URL + "/")
        response.raise_for_status()
        return response.json()


# ADD a news item
async def add_news(title: str, link: str, source: str, topic_id: int | None = None) -> Dict:
    async with httpx.AsyncClient() as client:
        payload = {
            "title": title,
            "link": link,
            "source": source,
            "topic_id": topic_id,
        }
        response = await client.post(BASE_URL + "/", json=payload)
        response.raise_for_status()
        return response.json()


# UPDATE a news item
async def update_news(news_id: int, title: str | None = None, link: str | None = None,
                      source: str | None = None, topic_id: int | None = None) -> Dict:

    async with httpx.AsyncClient() as client:
        payload = {
            "title": title,
            "link": link,
            "source": source,
            "topic_id": topic_id,
        }

        # Remove all None fields (only update supplied values)
        payload = {k: v for k, v in payload.items() if v is not None}

        response = await client.put(f"{BASE_URL}/{news_id}", json=payload)
        response.raise_for_status()
        return response.json()


# DELETE news (hard delete)
async def delete_news(news_id: int) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{BASE_URL}/{news_id}")
        response.raise_for_status()
        return response.json()


# For testing directly
if __name__ == "__main__":
    asyncio.run(get_all_news())
