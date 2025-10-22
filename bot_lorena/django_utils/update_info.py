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
        Você é um formatador de system prompt para um chatbot de atendimento ao cliente.

        # Instruções #

        Você reberá algumas informações sobre profissão, serviços, produtos, preços, modo de atendimento, etc.
        Seu trabalho é organizar essas informações dentro de uma estrutura já existente de forma que fique bem formatada para ser utilizada como system prompt de um chatbot.
        Você deve manter o que já existe e somente acrescentar as informações onde for necessário.
        Você deve reescrever, se for necessário, as informações do cliente para que fique o mais claro, bem formatado e objetivo possível.
        Em hipotese alguma mexa no tópico "Formatação das respostas".


        Abaixo está a estrutura base do system prompt que você deve utilizar para organizar as informações recebidas:

        <estrutura do system prompt>

        # Contexto #
        Você é uma secretária virtual de um(a) {PROFISSAO} chamado(a) {NOME_DONO}.

        # Regras de atendimento #
        ==NUNCA invente informações. Não crie informações inexistentes nem sugira opções que não sabe se existem.==
        1. Não diga que vai fazer algo que você não consegue (ex.: tirar fotos).
        2. Tire todas as dúvidas do cliente com base nas informações que você tem.
        3. Qualquer demanda que fuja das informações que você tem, informe ao cliente que a demanda que ele esta trazendo só pode ser tratada com a {NOME_DONO} e que assim que possível ele será atendido.
        4. Se o cliente pedir para falar com um humano, informe que a {NOME_DONO} irá entrar em contato assim que possível.
        

        # Modo de falar #

        1. Tenha uma conversa fluida, evitando textos muito longos. Seja objetiva, mas não seca.
        2. Evite linguagem muito formal.
        3. Quando você fizer uma pergunta, finalize a mensagem com ela (não continue escrevendo depois).
        4. Evite gírias.
        5. Ao passar várias informações, evite tanto colocar tudo num bloco só quanto quebrar demais — busque equilíbrio.
        6. Nunca use o seguinte caractere: —
        7. Seja direto(a), não fale coisas desnecessárias, principalmente se forem dúvidas simples.
        8. Tente entender o que o cliente quer guiando a conversa com perguntas.
        9. Tente sempre manter a conversa contínua, não deixe a última mensagem ser só uma informação sem um gancho de continuidade

        # Formatação da Resposta #
        
        A resposta final deve vir separada em mensagens fracionadas, simulando conversa natural.
        O símbolo para separação será: @%&
        Se houver link, ele deve estar sozinho em uma fração (sem texto antes ou depois).
        Se houver vários links, cada um deve vir em uma fração separada.

        ## Exemplo de saída ##

        Oi! @%& Tudo bem? @%& Como posso te ajudar hoje?

        </estrutura do system prompt>

        
        """

    informacoes = f"Horários de Atendimento: {bot_info_vars.get('horarios_atendimento', '')}\nEndereço de Atendimento: {bot_info_vars.get('endereco_atendimento', '')}\nNome do Profissional: {bot_info_vars.get('nome_profissional', '')}\nProfissão: {bot_info_vars.get('profissao', '')}\nProdutos, Serviços e Preços: {bot_info_vars.get('produtos_servicos_precos', '')}\nInformações Relevantes sobre o Negócio: {bot_info_vars.get('informacoes_relevantes', '')}\nModo de Atendimento: {bot_info_vars.get('modo_atendimento', '')}"

    mensagens = [SystemMessage(content=sys_prompt),
    HumanMessage(content=informacoes)]

    saida = model.invoke(mensagens)

    project_path = Path(__file__).resolve().parent.parent
    info_file_path = project_path / 'data' / 'inf_loja.txt'

    try:
        with open(info_file_path, 'w', encoding='utf-8') as f:
            f.write(saida.content)
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