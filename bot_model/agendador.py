import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
import time
from datetime import datetime, timedelta
import httpx
import asyncio
import re

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    env_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)

    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host='localhost',  # Conectando ao serviço do docker
            port='5432'
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

def get_scheduled_messages():
    """Busca mensagens agendadas nos últimos 10 minutos."""
    conn = get_db_connection()
    if not conn:
        return []

    messages = []
    try:
        with conn.cursor() as cur:
            # Define o período de 10 minutos atrás a partir do tempo atual
            ten_minutes_ago = datetime.now() - timedelta(minutes=10)
            
            cur.execute("""
                SELECT id, phone_number, message
                FROM onboarding_automatedmessage
                WHERE send_at >= %s AND send_at <= NOW();
            """, (ten_minutes_ago,))
            
            results = cur.fetchall()
            for row in results:
                phone_number = '55' + re.sub(r'\D', '', row[1]) + '@s.whatsapp.net'
                messages.append({
                    'id': row[0],
                    'phone_number': phone_number,
                    'message': row[2]
                })
    except Exception as e:
        print(f"Erro ao buscar mensagens: {e}")
    finally:
        if conn:
            conn.close()
    return messages

async def send_message(sender: str, message_text: str):
    """Envia a mensagem via Evolution API."""
    load_dotenv()
    INSTANCIA_EVOLUTION_API = os.getenv("INSTANCIA_EVOLUTION_API")
    EVOLUTION_TEXT_URL_TEMPLATE = os.getenv("EVOLUTION_TEXT_URL")
    EVOLUTION_PORT = os.getenv("EVOLUTION_PORT")
    EVOLUTION_TEXT_URL = EVOLUTION_TEXT_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, EVOLUTION_PORT=EVOLUTION_PORT)
    EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")

    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    payload = {
        "number": sender,
        "type": "text",
        "text": message_text
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(EVOLUTION_TEXT_URL, json=payload, headers=headers, timeout=30)
            if response.status_code == 200 or response.status_code == 201:
                print(f"Mensagem enviada com sucesso para {sender}")
                return True
            else:
                print(f"Falha ao enviar mensagem para {sender}: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"Erro na requisição para a API: {e}")
        return False

def delete_message(message_id: int):
    """Deleta a mensagem do banco de dados após o envio."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM onboarding_automatedmessage WHERE id = %s;", (message_id,))
        conn.commit()
        print(f"Mensagem ID {message_id} deletada do banco de dados.")
    except Exception as e:
        print(f"Erro ao deletar mensagem ID {message_id}: {e}")
    finally:
        if conn:
            conn.close()

async def check_and_send_messages():
    """Função principal que coordena a verificação e o envio."""
    print(f"[{datetime.now()}] Verificando mensagens agendadas...")
    messages_to_send = get_scheduled_messages()

    if not messages_to_send:
        print("Nenhuma mensagem para enviar no momento.")
        return

    for msg in messages_to_send:
        success = await send_message(msg['phone_number'], msg['message'])
        if success:
            delete_message(msg['id'])

if __name__ == '__main__':
    while True:
        try:
            asyncio.run(check_and_send_messages())
        except Exception as e:
            print(f"Ocorreu um erro no loop principal: {e}")
        
        # Aguarda 5 minutos (300 segundos) para a próxima verificação
        print("Aguardando 5 minutos para a próxima verificação...")
        time.sleep(300)