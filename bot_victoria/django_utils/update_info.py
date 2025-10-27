import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
import sys
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Conecta-se ao banco de dados PostgreSQL."""
    # Carrega o arquivo .env da pasta principal do projeto
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)

    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host='postgres',  # Nome do serviço no docker-compose
            port='5432'
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao Banco de Dados: {e}", file=sys.stderr)
        return None

def fetch_bot_info(username: str):
    """Busca as informações do bot do usuário e retorna como dicionário de variáveis."""
    conn = get_db_connection()
    if not conn:
        return None

    bot_info_vars = {}
    
    try:
        with conn.cursor() as cur:
            # Busca todas as informações do bot associado ao username
            cur.execute("""
                SELECT 
                    bi.horarios_atendimento,
                    bi.endereco_atendimento,
                    bi.nome_profissional,
                    bi.profissao,
                    bi.produtos_servicos_precos,
                    bi.informacoes_relevantes,
                    bi.modo_atendimento
                FROM onboarding_botinfo bi
                JOIN auth_user au ON bi.user_id = au.id
                WHERE au.username = %s;
            """, (username,))
            
            result = cur.fetchone()
            
            if result:
                # Atribui cada campo a uma variável
                bot_info_vars['horarios_atendimento'] = result[0] or ''
                bot_info_vars['endereco_atendimento'] = result[1] or ''
                bot_info_vars['nome_profissional'] = result[2] or ''
                bot_info_vars['profissao'] = result[3] or ''
                bot_info_vars['produtos_servicos_precos'] = result[4] or ''
                bot_info_vars['informacoes_relevantes'] = result[5] or ''
                bot_info_vars['modo_atendimento'] = result[6] or ''
                
                print(f"✓ Informações carregadas com sucesso para o usuário '{username}'")
                return bot_info_vars
            else:
                print(f"Não foram encontradas informações para o usuário '{username}'")

    except Exception as e:
        print(f"Erro ao buscar informações do bot: {e}", file=sys.stderr)

def formata_bot_info(bot_info_vars):
    """Passa as informações pelo modelo para formatar melhor"""

    model = ChatOpenAI(model="gpt-4.1", max_tokens=1200)

    sys_prompt = """

        # Contexto #
        Você é um especialista em formatar textos para system prompts de chatbots.

        # Instruções #

        - Você reberá algumas informações sobre profissão, serviços, produtos, preços, modo de atendimento, etc.
        - Seu trabalho é organizar essas informações de forma que fique bem formatada para ser utilizada como system prompt de um chatbot.
        - Você deve reescrever as informações do cliente para que fique o mais claro, bem formatado e objetivo possível.
        - O texto que você gerar será encaixado em um system prompt, onde já terá o contexto de ser uma secretária virtual.
        """

    informacoes = f"Horários de Atendimento: {bot_info_vars.get('horarios_atendimento', '')}\nEndereço de Atendimento: {bot_info_vars.get('endereco_atendimento', '')}\nNome do Profissional: {bot_info_vars.get('nome_profissional', '')}\nProfissão: {bot_info_vars.get('profissao', '')}\nProdutos, Serviços e Preços: {bot_info_vars.get('produtos_servicos_precos', '')}\nInformações Relevantes sobre o Negócio: {bot_info_vars.get('informacoes_relevantes', '')}\nModo de Atendimento: {bot_info_vars.get('modo_atendimento', '')}"

    mensagens = [SystemMessage(content=sys_prompt),
    HumanMessage(content=informacoes)]

    saida = model.invoke(mensagens)

    project_path = Path(__file__).resolve().parent.parent
    info_file_path = project_path / 'data' / 'inf_loja.txt'
    template_file_path = project_path / 'data' / 'template.txt'

    try:
        with open(template_file_path, 'r', encoding='utf-8') as f:
            template_file = f.read()
        prompt = template_file.replace("{PROFISSAO}", bot_info_vars.get('profissao', ''))
        prompt = prompt.replace("{NOME_DONO}", bot_info_vars.get('nome_profissional', ''))
        prompt = prompt.replace("{INFORMACOES_BOT}", saida.content)


        with open(info_file_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"✓ Informações do bot salvas com sucesso em '{info_file_path}'")
    except Exception as e:
        print(f"Erro ao salvar informações do bot: {e}", file=sys.stderr)




if __name__ == '__main__':
    # O nome de usuário será passado como um argumento quando o script for chamado
    if len(sys.argv) > 1:
        bot_username = sys.argv[1]
        info = fetch_bot_info(bot_username)
        if info:
            formata_bot_info(info)
    else:
        print("Erro: Nome de usuário não foi fornecido.", file=sys.stderr)
        sys.exit(1)