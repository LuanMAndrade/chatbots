import redis.asyncio as redis
import asyncio

tempo_pausa = 3600 #1h

async def congelamento(data, sender, redis_client):

    if data["data"]["key"].get("fromMe") == True:
        await redis_client.setex(name=sender, time=tempo_pausa, value="pausado")
        
        print(f"PAUSA ativada para {sender} por {tempo_pausa} segundos via Redis", flush=True)
        return True
    pausou = await verifica_congelamento(sender, redis_client)
    return pausou


async def verifica_congelamento(sender, redis_client):
    if await redis_client.exists(sender):
        print(f"Em pausa para este número", flush=True)
        return True
    return False