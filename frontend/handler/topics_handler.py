# topics_handler.py
import asyncio
import httpx
from typing import List, Dict

# Base URL of your FastAPI server
BASE_URL = "http://localhost:8000/topics/api/topics"


# GET all topics
async def get_all_topics() -> List[Dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(BASE_URL + "/")
        response.raise_for_status()
        return response.json()


# ADD new topic
async def add_topic(topic_name: str) -> Dict:
    async with httpx.AsyncClient() as client:
        payload = {"topic_name": topic_name}
        response = await client.post(BASE_URL + "/", json=payload)
        response.raise_for_status()
        return response.json()


# UPDATE topic active_flag
async def update_topic_flag(topic_id: int, active_flag: str) -> Dict:
    async with httpx.AsyncClient() as client:
        payload = {"active_flag": active_flag}
        response = await client.put(f"{BASE_URL}/{topic_id}", json=payload)
        response.raise_for_status()
        return response.json()


# DELETE topic (soft delete)
async def delete_topic(topic_id: int) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{BASE_URL}/{topic_id}")
        response.raise_for_status()
        return response.json()



if __name__ == "__main__":
    asyncio.run(get_all_topics())