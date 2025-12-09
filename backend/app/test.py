import aiohttp
import asyncio

async def fetch_rss(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"⚠️ Error fetching {url}: {resp.status}")
            return await resp.text()

async def main():
    url = "https://3dprint.com/feed"
    try:
        data = await fetch_rss(url)
        print("✅ RSS fetched, length:", len(data))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
