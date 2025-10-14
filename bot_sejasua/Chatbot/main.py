from fastapi import FastAPI, Request
import asyncio
import redis.asyncio as redis
from process_message.process_message import process_message
from woocommerce import woocommerce
import os

from data_base.estoque import cria_estoque



redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6380)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)



#___________________________________________________________________________________________________________________

app = FastAPI()

@app.post("/whatsapp")
async def whatsapp(request: Request):
    data = await request.json()

    # Cria tarefa assíncrona
    asyncio.create_task(process_message(data, redis_client))

    # Retorna imediatamente para evitar eco
    return {"status": "ok"}
    

@app.post("/erp")
async def woocommerce_webhook(request: Request):
    data = await request.json()
    print(data)
    asyncio.create_task(woocommerce(data))
    return {"status": "ok"}
    



    
