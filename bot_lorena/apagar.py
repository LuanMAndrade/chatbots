import redis.asyncio as redis
import os
import asyncio




redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6380,
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)

async def apagar_chave():
    sender = '5521980330995@s.whatsapp.net'
    data = await redis_client.delete(sender)
    print(data)
    await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(apagar_chave())