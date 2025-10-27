from langchain_core.tools import tool
from typing import Annotated
import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

NUMERO_AGENDAMENTO = os.getenv('NUMERO_AGENDAMENTO')
NUMERO_BIOPSIA = os.getenv('NUMERO_BIOPSIA')
INSTANCIA_EVOLUTION_API = os.getenv("INSTANCIA_EVOLUTION_API")
EVOLUTION_TEXT_URL_TEMPLATE = os.getenv("EVOLUTION_TEXT_URL")
EVOLUTION_PORT = os.getenv("EVOLUTION_PORT")
EVOLUTION_TEXT_URL = EVOLUTION_TEXT_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, EVOLUTION_PORT=EVOLUTION_PORT)
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")

async def chama_agendamento(nome):
    async with httpx.AsyncClient() as client:
        nome = nome.split('@')[0]
        payload = {"number": NUMERO_AGENDAMENTO,
                    "text": f"A cliente {nome} quer fazer um agendamento"}
        headers = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
                }
        await client.post(EVOLUTION_TEXT_URL, json=payload, headers=headers)

async def chama_biopsia(nome):
    async with httpx.AsyncClient() as client:
        nome = nome.split('@')[0]
        payload = {"number": NUMERO_BIOPSIA,
                    "text": f"A cliente {nome} quer fazer uma biópsia"}
        headers = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
                }
        await client.post(EVOLUTION_TEXT_URL, json=payload, headers=headers)



@tool
def agendamento_normal(nome: Annotated[str, "Número de identificação do cliente"]):
    """Faz um agendamento normal"""
    asyncio.run(chama_agendamento(nome))

    return "Informe para aguardar um momento enquanto transfere o atendimento para o setor de agendamentos. Fale somente isso, nada mais."

@tool
def agendamento_biopsia(nome: Annotated[str, "Número de identificação do cliente"]):
    """Faz um agendamento de biópsia"""
    asyncio.run(chama_biopsia(nome))

    return "Informe para aguardar um momento enquanto transfere o atendimento para o setor de agendamentos. Fale somente isso, nada mais."