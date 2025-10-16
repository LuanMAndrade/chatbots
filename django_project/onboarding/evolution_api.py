import os
import requests
import logging
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

def get_whatsapp_contacts(username):
    """
    Busca contatos de um projeto específico no banco de dados do Evolution API.

    Args:
        project_name: O nome do projeto (ex: 'bot_model').
    """
    # Carrega as variáveis de ambiente do arquivo .env na pasta raiz
    env_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)

    instance_name = f"bot_{username}"
    
    # Conecta ao banco de dados usando as credenciais do .env
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host='postgres',  # Nome do serviço no docker-compose
        port='5432'
    )
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
            "name",
            "id"
            FROM
            public."Instance";
            """)
        instancias = cur.fetchall()

        print(instancias)

        for instancia in instancias:
            if instancia[0] == instance_name:
                instance_id = instancia[1]
                break

        print(instance_id)

        # Executa a consulta SQL
        cur.execute("""
        SELECT
        "remoteJid",
        "pushName"
        FROM
        public."Contact"
        WHERE "instanceId" = %s""", (instance_id,))
        contacts = cur.fetchall()
    
    contatos = []

    for contato in contacts:
        phone = contato[0].split('@')[0]
        item = {"name": contato[1], "phone": phone, "id": contato[1]}
        contatos.append(item)

    return contatos


if __name__ == "__main__":
    contatos = get_whatsapp_contacts('model')
    print(contatos)