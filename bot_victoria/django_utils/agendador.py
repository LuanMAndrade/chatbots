import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
import time
from datetime import datetime, timedelta
import httpx
import asyncio
import re
import sys

# Carrega variáveis de ambiente
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

print(f"[{datetime.now()}] 🚀 Iniciando serviço de agendamento de mensagens...", flush=True)
print(f"[{datetime.now()}] 📁 Carregando .env de: {env_path}", flush=True)

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    try:
        # CORREÇÃO: Usa localhost pois o script roda fora do Docker
        # mas o PostgreSQL está exposto na porta 5432 do host
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host='localhost',  # ALTERADO de 'postgres' para 'localhost'
            port='5432'
        )
        print(f"[{datetime.now()}] ✅ Conexão com banco de dados estabelecida", flush=True)
        return conn
    except psycopg2.OperationalError as e:
        print(f"[{datetime.now()}] ❌ Erro ao conectar ao PostgreSQL: {e}", flush=True)
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
                WHERE send_at >= %s 
                AND send_at <= NOW()
                AND status = 'pending';
            """, (ten_minutes_ago,))
            
            results = cur.fetchall()
            for row in results:
                phone_number = re.sub(r'\D', '', row[1])
                if not phone_number.startswith('55'):
                    phone_number = '55' + phone_number
                phone_number = phone_number + '@s.whatsapp.net'
                
                messages.append({
                    'id': row[0],
                    'phone_number': phone_number,
                    'message': row[2]
                })
            
            if results:
                print(f"[{datetime.now()}] 📬 Encontradas {len(messages)} mensagem(ns) para enviar", flush=True)
                
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Erro ao buscar mensagens: {e}", flush=True)
    finally:
        if conn:
            conn.close()
    return messages

async def send_message(sender: str, message_text: str):
    """Envia a mensagem via Evolution API."""
    INSTANCIA_EVOLUTION_API = os.getenv("INSTANCIA_EVOLUTION_API")
    EVOLUTION_TEXT_URL_TEMPLATE = os.getenv("EVOLUTION_TEXT_URL")
    EVOLUTION_PORT = os.getenv("EVOLUTION_PORT")
    EVOLUTION_TEXT_URL = EVOLUTION_TEXT_URL_TEMPLATE.format(
        INSTANCIA=INSTANCIA_EVOLUTION_API, 
        EVOLUTION_PORT=EVOLUTION_PORT
    )
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
            response = await client.post(
                EVOLUTION_TEXT_URL, 
                json=payload, 
                headers=headers, 
                timeout=30
            )
            if response.status_code == 200 or response.status_code == 201:
                print(f"[{datetime.now()}] ✅ Mensagem enviada com sucesso para {sender}", flush=True)
                return True
            else:
                print(f"[{datetime.now()}] ❌ Falha ao enviar mensagem para {sender}: {response.status_code} - {response.text}", flush=True)
                return False
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Erro na requisição para a API: {e}", flush=True)
        return False

def mark_message_as_sent(message_id: int):
    """Marca a mensagem como enviada no banco de dados."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE onboarding_automatedmessage 
                SET status = 'sent', sent_at = NOW() 
                WHERE id = %s;
            """, (message_id,))
        conn.commit()
        print(f"[{datetime.now()}] ✅ Mensagem ID {message_id} marcada como enviada.", flush=True)
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Erro ao atualizar mensagem ID {message_id}: {e}", flush=True)
    finally:
        if conn:
            conn.close()

def mark_message_as_failed(message_id: int):
    """Marca a mensagem como falha no banco de dados."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE onboarding_automatedmessage 
                SET status = 'failed' 
                WHERE id = %s;
            """, (message_id,))
        conn.commit()
        print(f"[{datetime.now()}] ⚠️ Mensagem ID {message_id} marcada como falha.", flush=True)
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Erro ao atualizar mensagem ID {message_id}: {e}", flush=True)
    finally:
        if conn:
            conn.close()

async def check_and_send_messages():
    """Função principal que coordena a verificação e o envio."""
    print(f"[{datetime.now()}] 🔍 Verificando mensagens agendadas...", flush=True)
    messages_to_send = get_scheduled_messages()

    if not messages_to_send:
        print(f"[{datetime.now()}] ℹ️ Nenhuma mensagem para enviar no momento.", flush=True)
        return

    for msg in messages_to_send:
        print(f"[{datetime.now()}] 📤 Processando mensagem ID {msg['id']} para {msg['phone_number']}", flush=True)
        success = await send_message(msg['phone_number'], msg['message'])
        if success:
            mark_message_as_sent(msg['id'])
        else:
            mark_message_as_failed(msg['id'])

if __name__ == '__main__':
    print("=" * 80, flush=True)
    print(f"[{datetime.now()}] 🤖 SERVIÇO DE AGENDAMENTO INICIADO", flush=True)
    print(f"[{datetime.now()}] ⏰ Verificação a cada 5 minutos", flush=True)
    print("=" * 80, flush=True)
    
    # Teste inicial de conexão
    test_conn = get_db_connection()
    if test_conn:
        test_conn.close()
        print(f"[{datetime.now()}] ✅ Teste de conexão com banco OK", flush=True)
    else:
        print(f"[{datetime.now()}] ❌ ATENÇÃO: Falha no teste de conexão com banco", flush=True)
        print(f"[{datetime.now()}] ℹ️ Verificando variáveis de ambiente...", flush=True)
        print(f"[{datetime.now()}] DB: {os.getenv('POSTGRES_DB')}", flush=True)
        print(f"[{datetime.now()}] USER: {os.getenv('POSTGRES_USER')}", flush=True)
        print(f"[{datetime.now()}] HOST: localhost:5432", flush=True)
    
    # Loop principal
    iteration = 0
    while True:
        try:
            iteration += 1
            print(f"\n[{datetime.now()}] 🔄 Iteração #{iteration}", flush=True)
            asyncio.run(check_and_send_messages())
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Ocorreu um erro no loop principal: {e}", flush=True)
            import traceback
            traceback.print_exc()
        
        # Aguarda 5 minutos (300 segundos) para a próxima verificação
        print(f"[{datetime.now()}] ⏳ Aguardando 5 minutos para a próxima verificação...", flush=True)
        time.sleep(300)