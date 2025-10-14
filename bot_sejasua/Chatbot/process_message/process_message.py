import redis.asyncio as redis
from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv
import asyncio
import sqlite3
from langchain_core.messages import HumanMessage
import base64
import random
import json
import re

from process_message.buffer import buffer_message
from process_message.congelamento import congelamento
from process_message.process_audio import process_audio
from process_message.salva_id_imagem import salva_id_imagem, busca_imagem
from graph.graph import build_chat_graph
from data_base.message_history import init_db

load_dotenv()

INSTANCIA_EVOLUTION_API = os.getenv("INSTANCIA_EVOLUTION_API")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
PORTA = os.getenv("PORTA")

# Link para texto
EVOLUTION_TEXT_URL_TEMPLATE = os.getenv("EVOLUTION_TEXT_URL")
EVOLUTION_TEXT_URL = EVOLUTION_TEXT_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, PORTA=PORTA)

# Link para o "digitando..."
EVOLUTION_PRESENCE_URL_TEMPLATE = os.getenv("EVOLUTION_PRESENCE_URL")
EVOLUTION_PRESENCE_URL = EVOLUTION_PRESENCE_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, PORTA=PORTA)

# Link para midia
EVOLUTION_MEDIA_URL_TEMPLATE = os.getenv("EVOLUTION_MEDIA_URL")
EVOLUTION_MEDIA_URL = EVOLUTION_MEDIA_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, PORTA=PORTA)

LOCK_TTL = 300   # segundos

headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
        }



async def process_message(data, redis_client):

    print(f'Dados recebidos: {data}', flush= True)

    message_id = data["data"]["key"].get("id")
    lock_key = f"lock:{message_id}"
    if await redis_client.exists(lock_key):
        print(f"Mensagem {message_id} já processada. Ignorando.", flush= True)
        return

    await redis_client.setex(lock_key, LOCK_TTL, 1)

    init_db()

    # Identifica o remetente, é necessário por questões de privacidade do whatsapp
    # _________________________________________________________________________

    if "@lid" in data["data"]["key"]["remoteJid"]:
       sender = data["data"]["key"].get("senderPn")
    else:
       sender = data["data"]["key"].get("remoteJid")

    message_data = data["data"].get("message", {})
    nome = data["data"].get("pushName", "")

    # _________________________________________________________________________
    # Pausa no atendimento caso o humano assuma

    pausou = congelamento(data, sender)
    if pausou:
        return pausou
    
    # _________________________________________________________________________
    # Verifica se é audio ou mensagem e trata o dado


    if "audioMessage" in message_data:
        message = await asyncio.to_thread(process_audio, message_data)
    elif "conversation" in message_data:
        message = message_data["conversation"]
    else:
        return None

    
    # _________________________________________________________________________
    # Verifica se a mensagem está se referindo a alguma anterior
    if data["data"].get('contextInfo'):
        if "quotedMessage" in data["data"]['contextInfo']:
            if "conversation" in data["data"]['contextInfo']["quotedMessage"]:
                message = f"Respondendo sua mensagem anterior: '{data["data"]['contextInfo']["quotedMessage"].get("conversation")}'\nMinha resposta: {message}"
            elif "imageMessage" in data["data"]['contextInfo']["quotedMessage"]:
                id_imagem = data["data"]['contextInfo'].get('stanzaId')
                print(f"!!!!!!!!!!!! {id_imagem}",flush= True)
                link_imagem = await busca_imagem(id_imagem)
                message = f"Respondendo sua mensagem anterior: '{link_imagem}'\nMinha resposta: {message}"

    # _________________________________________________________________________
    # Adiciona mensagem no buffer

    buffer = await buffer_message(redis_client, sender, message)
    if buffer:
        final_text = buffer
    else:
        return {"status": "aguardando"}

    #__________________________________________________________________________
    # Invoca o grapho e divide a resposta

    config = {"configurable": {"conversation_id": sender}}
    chat_graph = build_chat_graph()
    respostas = chat_graph.invoke({"messages": [HumanMessage(content=final_text)],}, config=config)
    ultima_resposta = respostas["messages"][-1].content
    lista_de_mensagens = ultima_resposta.split("$%&$")

    #____________________________________________________________________________________________________________________________________________________________________________________________________________________
    # Envia a mensagem parte a parte

    async with httpx.AsyncClient() as client:
            
        for parte in lista_de_mensagens:
            parte = parte.strip()

            #_____________________________________________________________________
            # Configurando o "Digitando..."
        
            typing_url = EVOLUTION_PRESENCE_URL 
            tempo_digitando = len(parte)*1000/17
            
            if tempo_digitando > 6000:
                tempo_digitando = 6000
            elif tempo_digitando < 1000:
                tempo_digitando = 1000

            print(f"tempo_digitando: {tempo_digitando}", flush = True)

            typing_payload = {
                "number": sender,
                'delay':tempo_digitando,
                'presence':'composing'}

            await client.post(typing_url, json=typing_payload, headers=headers, timeout=30)

            #_____________________________________________________________________
            # Montando o payload para enviar a mensagem

            # Se for link de imagem vai nesse payload
            extensoes = ['.png', '.jpg', '.jpeg', '.webp']
            if any(ext in parte for ext in extensoes):
                pattern = r"(http[^\s]+(?:{}))".format("|".join([re.escape(ext) for ext in extensoes]))
                matches = re.findall(pattern, parte)

                for parte in matches:
                    payload = {
                        "number": sender,
                        "mediatype": "image",
                        "caption": "",
                        "media": parte
                        }
                    url = EVOLUTION_MEDIA_URL

                    response = await client.post(url, json=payload, headers=headers, timeout=30)
                    print("Resposta enviada:", parte, "-", response.status_code, flush= True)
                    print(f"Response {response.json()}", flush = True)
                    id_imagem = response.json()['key'].get('id')
                    print(f"Resposta FULL: {id_imagem}", flush= True)
                    if url == EVOLUTION_MEDIA_URL:
                        await salva_id_imagem(sender, id_imagem, parte)
                    tempo_espera = random.randint(1, 3)
                    await asyncio.sleep(tempo_espera)
            
            # Se for texto vai nesse payload
            else:
                payload = {
                    "number": sender,
                    "type": "text",
                    "text": parte
                    }
                url = EVOLUTION_TEXT_URL


                response = await client.post(url, json=payload, headers=headers, timeout=30)
                print("Resposta enviada:", parte, "-", response.status_code, flush= True)
                id_imagem = response.json()['key'].get('id')
                print(f"Resposta FULL: {id_imagem}", flush= True)
                if url == EVOLUTION_MEDIA_URL:
                    await salva_id_imagem(sender, id_imagem, parte)
                tempo_espera = random.randint(1, 3)
                await asyncio.sleep(tempo_espera)