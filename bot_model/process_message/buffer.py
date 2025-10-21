import asyncio

BUFFER_TTL = 1

async def buffer_message(redis_client, sender, message):
    buffer_key = f"ram:{sender}"
    current_text = await redis_client.get(buffer_key) or ""
    new_text = f"{current_text}\n{message}".strip()
    await redis_client.setex(buffer_key, BUFFER_TTL+1, new_text)
    

    # Espera o tempo do buffer para ver se chegam mais mensagens
    await asyncio.sleep(BUFFER_TTL)

    final_text = await redis_client.get(buffer_key)

    if final_text == new_text:
        # ninguém enviou mais nada -> processa
        await redis_client.delete(buffer_key)
        return final_text
    else:
        return False