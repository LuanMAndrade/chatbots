import asyncio
import os
from dotenv import load_dotenv
import httpx
import sys        
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo


load_dotenv()

NUMERO_BACKUP = os.getenv('NUMERO_BACKUP')
INSTANCIA_EVOLUTION_API = os.getenv("INSTANCIA_EVOLUTION_API")
EVOLUTION_TEXT_URL_TEMPLATE = os.getenv("EVOLUTION_TEXT_URL")
EVOLUTION_PORT = os.getenv("EVOLUTION_PORT")
EVOLUTION_TEXT_URL = EVOLUTION_TEXT_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, EVOLUTION_PORT=EVOLUTION_PORT)
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
NUMERO_PARA_ERROS = os.getenv("NUMERO_PARA_ERROS")

async def agendamento(data):

    try:
        async with httpx.AsyncClient() as client:
            payload = data.get('payload')
            if payload:
                attendees = payload.get('attendees')
                onde = payload.get('eventTitle')
                metadata = payload.get('metadata')
                if metadata:
                    link = metadata.get('videoCallUrl')
                inicio = payload.get('startTime')
                dt_utc = datetime.fromisoformat(inicio)
                brasilia_tz = ZoneInfo("America/Sao_Paulo")
                dt_brasilia = dt_utc.astimezone(brasilia_tz)
                inicio = dt_brasilia.strftime('%d/%m/%Y %H:%M:%S')
                fim = payload.get('endTime')
                dt_utc = datetime.fromisoformat(fim)
                brasilia_tz = ZoneInfo("America/Sao_Paulo")
                dt_brasilia = dt_utc.astimezone(brasilia_tz)
                fim = dt_brasilia.strftime('%d/%m/%Y %H:%M:%S')
                if attendees:
                    sender = attendees[0].get('phoneNumber')
                    sender = f'{sender[1:]}@s.whatsapp.net'
                    if data.get('triggerEvent') == 'BOOKING_CREATED':
                        text = f"Verifiquei aqui que você agendou um {onde} das {inicio} às {fim}.\n\n Guarde este link para entrar na reunião:\n{link} "
                    elif data.get('triggerEvent') == 'BOOKING_CANCELLED':
                        text = f"Verifiquei aqui que você cancelou o {onde} das {inicio} às {fim}"
                    else:
                        return True
                    payload = {"number": sender,
                                "text": text}
                    headers = {
                            "Content-Type": "application/json",
                            "apikey": EVOLUTION_API_KEY
                            }
                    await client.post(EVOLUTION_TEXT_URL, json=payload, headers=headers)
            return True
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        arquivo = exc_tb.tb_frame.f_code.co_filename
        linha = exc_tb.tb_lineno

        print("\n--- ERRO CAPTURADO ---", flush = True)
        print(f"Ocorreu um erro do tipo: {exc_type.__name__}", flush = True)
        print(f"No arquivo: {arquivo}", flush = True)
        print(f"Na linha: {linha}", flush = True)
        print(f"Mensagem: {e}", flush = True)
        print("-----------------------------------------------", flush = True)

        async with httpx.AsyncClient() as client:
            headers = {
                    "Content-Type": "application/json",
                    "apikey": EVOLUTION_API_KEY
                    }
            payload = {
                        "number": NUMERO_PARA_ERROS,
                        "type": "text",
                        "text": f"*Houve um erro no projeto: {INSTANCIA_EVOLUTION_API}*\nOcorreu um erro do tipo: {exc_type.__name__}\nNo arquivo: {arquivo}\nNa linha: {linha}\nMensagem: {e}"
                        }
            await client.post(EVOLUTION_TEXT_URL, json=payload, headers=headers, timeout=30)
