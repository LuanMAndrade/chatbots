from langchain_core.tools import tool
from typing import Annotated
import asyncio
import os
from dotenv import load_dotenv
import httpx

from graph.carrinho import remove_from_cart2

load_dotenv()

NUMERO_BACKUP = os.getenv('NUMERO_BACKUP')
INSTANCIA_EVOLUTION_API = os.getenv("INSTANCIA_EVOLUTION_API")
EVOLUTION_TEXT_URL_TEMPLATE = os.getenv("EVOLUTION_TEXT_URL")
PORTA = os.getenv("PORTA")
EVOLUTION_TEXT_URL = EVOLUTION_TEXT_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, PORTA=PORTA)
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")

async def chama_clara(nome, produto):
    async with httpx.AsyncClient() as client:
        payload = {"number": NUMERO_BACKUP ,
                    "text": f"A cliente {nome}, quer fazer o pagamento do produto {produto}"}
        headers = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
                }
        await client.post(EVOLUTION_TEXT_URL, json=payload, headers=headers)



@tool
def pagamento(nome: Annotated[str, "Número de identificação do cliente"], produto:Annotated[str, "Produtos para finalizar"]):
    """Retorna um link de pagamento para a cliente."""
    asyncio.run(chama_clara(nome, produto))
    remove_from_cart2(nome)

    return "Informe que apartir de agora o atendimento será finalizado por uma do financeiro. Fale somente isso, nada mais."