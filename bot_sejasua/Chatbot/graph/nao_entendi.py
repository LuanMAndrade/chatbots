from langchain_core.tools import tool
from typing import Annotated
import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

NUMERO_BACKUP = os.getenv('NUMERO_BACKUP')
INSTANCIA_EVOLUTION_API = os.getenv("INSTANCIA_EVOLUTION_API")
EVOLUTION_TEXT_URL_TEMPLATE = os.getenv("EVOLUTION_TEXT_URL")
PORTA = os.getenv("PORTA")
EVOLUTION_TEXT_URL = EVOLUTION_TEXT_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, PORTA=PORTA)
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")

async def chama_clara(nome):
    async with httpx.AsyncClient() as client:
        payload = {"number": NUMERO_BACKUP+'@s.whatsapp.net',
                    "text": f"Não estou entendendo o que a cliente {nome} quer"}
        headers = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
                }
        await client.post(EVOLUTION_TEXT_URL, json=payload, headers=headers)



@tool
def nao_entendi(nome: Annotated[str, "Número de identificação do cliente"]):
    """Informa a um atendente humano que não entendeu o que a cliente quer"""
    asyncio.run(chama_clara(nome))

    return "Informe que não conseguiu compreender e que irá transferir o atendimento para um humano. Fale somente isso, nada mais."