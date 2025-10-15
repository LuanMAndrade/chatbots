import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    # Garante que o .env na pasta principal do projeto seja carregado
    env_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)

    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host='localhost',  # ou o IP/host do seu DB se não for local
            port='5432'
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

def get_bot_info(username: str):
    """Busca as informações do bot para um usuário específico."""
    conn = get_db_connection()
    if not conn:
        return None
        
    info = None
    try:
        with conn.cursor() as cur:
            # A query junta as tabelas de info, user e busca pelo username
            cur.execute("""
                SELECT bi.info_text
                FROM onboarding_botinfo bi
                JOIN auth_user au ON bi.user_id = au.id
                WHERE au.username = %s;
            """, (username,))
            result = cur.fetchone()
            if result:
                info = result[0]
    finally:
        conn.close()
    return info

def get_automated_messages(username: str):
    """Busca todas as mensagens automáticas agendadas para um usuário."""
    conn = get_db_connection()
    if not conn:
        return []

    messages = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT am.phone_number, am.message, am.send_at
                FROM onboarding_automatedmessage am
                JOIN auth_user au ON am.user_id = au.id
                WHERE au.username = %s;
            """, (username,))
            results = cur.fetchall()
            for row in results:
                messages.append({
                    'phone_number': row[0],
                    'message': row[1],
                    'send_at': row[2]
                })
    finally:
        conn.close()
    return messages

# Exemplo de como usar as funções
if __name__ == '__main__':
    # Supondo que este script está dentro de uma pasta como 'bot_jorge'
    # O nome de usuário é extraído do nome da pasta pai.
    current_bot_username = Path(__file__).resolve().parent.name.replace('bot_', '')
    
    print(f"--- Buscando dados para o bot: {current_bot_username} ---")
    
    informacoes = get_bot_info(current_bot_username)
    if informacoes:
        print("\n[Informações do Bot]")
        print(informacoes)
    else:
        print("\nNenhuma informação encontrada para este bot.")

    agendamentos = get_automated_messages(current_bot_username)
    if agendamentos:
        print("\n[Mensagens Agendadas]")
        for msg in agendamentos:
            print(f"- Para: {msg['phone_number']} em {msg['send_at']:%d/%m/%Y %H:%M}")
            print(f"  Mensagem: {msg['message']}")
    else:
        print("\nNenhuma mensagem agendada.")