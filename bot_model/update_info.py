import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
import sys

def get_db_connection():
    """Conecta-se ao banco de dados PostgreSQL."""
    # Carrega o arquivo .env da pasta principal do projeto
    env_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)

    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host='localhost', # Conecta via localhost, pois o script roda no mesmo servidor
            port='5432'
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao Banco de Dados: {e}", file=sys.stderr)
        return None

def fetch_and_save_bot_info(username: str):
    """Busca as informações do usuário e salva em um arquivo local."""
    conn = get_db_connection()
    if not conn:
        return

    info_text = None
    try:
        with conn.cursor() as cur:
            # Busca o texto de informação associado ao username
            cur.execute("""
                SELECT bi.info_text
                FROM onboarding_botinfo bi
                JOIN auth_user au ON bi.user_id = au.id
                WHERE au.username = %s;
            """, (username,))
            result = cur.fetchone()
            if result:
                info_text = result[0]
    finally:
        conn.close()

    if info_text is not None:
        # Define o caminho /data/inf_loja2.txt dentro da pasta do bot
        data_folder = Path(__file__).resolve().parent / 'data'
        os.makedirs(data_folder, exist_ok=True)
        info_file_path = data_folder / 'inf_loja2.txt'
        
        # Salva a informação no arquivo
        with open(info_file_path, "w", encoding='utf-8') as f:
            f.write(info_text)
        print(f"Informação para '{username}' atualizada com sucesso em: {info_file_path}")
    else:
        print(f"Nenhuma informação encontrada para o usuário '{username}'")

if __name__ == '__main__':
    # O nome de usuário será passado como um argumento quando o script for chamado
    if len(sys.argv) > 1:
        bot_username = sys.argv[1]
        fetch_and_save_bot_info(bot_username)
    else:
        print("Erro: Nome de usuário não foi fornecido.", file=sys.stderr)
        sys.exit(1)