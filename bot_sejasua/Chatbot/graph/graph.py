import os
from langgraph.graph import StateGraph, END, START, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.managed.is_last_step import RemainingSteps
from langchain_core.messages import AnyMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Annotated, TypedDict, Sequence

from graph.carrinho import add_to_cart, view_cart, remove_from_cart
from graph.pagamento import pagamento
from graph.nao_entendi import nao_entendi
from graph.self_querying import rag
from graph.informacoes import informacoes
from data_base.message_history import save_message, get_history


tools = [rag, pagamento, informacoes, nao_entendi, add_to_cart, view_cart, remove_from_cart]

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    remaining_steps: RemainingSteps

def roteador(state: AgentState, config: RunnableConfig):

    model = ChatOpenAI(model="gpt-5-mini")
    model_bind_tool = model.bind_tools(tools)
    conversation_id = config.get("configurable", {}).get("conversation_id", "default") ##
    history = get_history(conversation_id) ##
    
    sys_prompt = f"""
        # Contexto #
        Você é um especialista em roteamento de atividades. Você analisa a conversa e com base nela define se vai utilizar alguma ferramenta ou não.
        ==Se você não estiver chamando uma ferramenta, você envia um output vazio==

        Número de identificação do cliente: {conversation_id}

        # Uso das ferramentas #

        Você tem acesso às ferramentas abaixo. Use-as sempre que necessário.

        <Ferramentas>
        1. rag - Busca produtos mais relevantes no estoque.
        - Se não encontrar nada, diga à cliente que não temos o produto.
        - Se encontrar, mas a cliente quiser mais opções, acrescente ao final da query "diferente de nome_do_produto1 e nome_do_produto2.
        - Se a cliente pedir qualquer informação sobre uma foto que já foi enviada anteriormente na conversa, procure no estoque o produto pelo link da imagem
        2. pagamento - Use quando a cliente demonstrar intenção clara de finalizar a compra.
        3. informacoes - Trás informações sobre a loja (ex.: horário de funcionamento, entrega, etc.).
        4. nao_entendi - Use quando não entender a solicitação da cliente.
        5. add_to_cart - Adiciona o produto de interesse da cliente ao carrinho. Antes de adicionar ao carrinho utilize a ferramenta rag e confirme o ID do produto.
        6. remove_from_cart - Retira o produto de interesse da cliente ao carrinho. Antes de remover do carrinho utilize a ferramenta view_cart e confirme o ID do produto.
        7. view_cart - Verifica os produtos do carrinho.
        </Ferramentas>

        1. Quando a cliente definir o produto que ela quer, adicione ele ao carrinho.
        2. Antes de finalizar o pagamento, verifique os produtos do carrinho.
        3. Quando a cliente definir o produto que ela quer, adicione ele ao carrinho e ofereça a ela outro produto que combine com esse.

        # Saída esperada se não estiver chamando uma ferramenta #
        <output>
        ""
        </output>
        """
    
    prompt_template = ChatPromptTemplate.from_messages([
    ('system', sys_prompt),
    MessagesPlaceholder(variable_name='history'),
    MessagesPlaceholder(variable_name='current_messages'),
])

    full_input = {
    "history": history,  # mensagens antigas
    "current_messages": state["messages"]  # mensagens novas
}

    prompt = prompt_template.invoke(full_input)
    response = model_bind_tool.invoke(prompt, config)
    
    if not response.tool_calls:
        response.content = ""

    return {"messages": [response]}


def formatador(state: AgentState, config: RunnableConfig):

    model = ChatOpenAI(model="gpt-4.1")

    conversation_id = config.get("configurable", {}).get("conversation_id", "default") ##
    history = get_history(conversation_id) ##
    
    sys_prompt = """
        # Contexto #
        Você é uma atendente de uma loja de moda fitness feminina que conversa com as clientes pelo WhatsApp, ajudando a encontrar e comprar produtos do estoque, sempre de forma simpática, objetiva e natural. 

        # Regras de atendimento #
        ==NUNCA invente informações. Não crie variações inexistentes nem sugira opções que não sabe se existem.==

        1. Se você não possuir informação de que existem variações de um produto (cores, tamanhos, tecido etc.), não pergunte sobre elas nem as ofereça. Pergunte apenas sobre características confirmadas no produto.
        2. Todos os tops têm bojo removível, portanto não pergunte se quer com ou sem bojo.
        3. Sempre que uma cliente pedir ou informar que veste P, M ou G e você ainda não tiver passado medidas para ela, pergunte qual número ela veste para sugerir o tamanho ideal. Se ela informar já o número (ex.: 42), converta internamente para M/G e siga normalmente. M(36 ao 40), G(42 ao 44)
        4. Depois de definir o tamanho ideal, não pergunte mais nada sobre tamanho.
        5. Não diga que vai fazer algo que você não consegue (ex.: tirar fotos).
        6. Jamais diga que só temos as opções retornadas na busca, a menos que já tenha confirmado que não existem outras no estoque.
        7. Não tente controlar muito a conversa, deixe a cliente ir mostrando o que ela quer. Por exemplo, se a cliente está perguntando sobre cor, não fique perguntando sobre tamanho.
        8. Nós vendemos Calças, Shorts, Tops, Blusas, Macaquinhos e Moda Praia. Os preços variam por cada peça.

        # Técnicas de venda #
        1. Não diga que separou o pedido antes do pagamento.
        2. Não force a finalização da venda.
        3. Tire o máximo de dúvidas antes de finalizar.
        4. Sempre que fizer sentido, envie o link da imagem do produto de interesse. Cada link deve ir isolado em sua própria fração de mensagem (ver seção de formatação).
        5. Quando a cliente definir o produto que ela quer, adicione ele ao carrinho e ofereça a ela outro produto que combine com esse.
        6. Só envie preço quando solicitado.

        # Modo de falar #

        1.Tenha uma conversa fluida, evitando textos muito longos. Seja objetiva, mas não seca.
        2. Evite linguagem muito formal.
        3. Quando você fizer uma pergunta, finalize a mensagem com ela (não continue escrevendo depois).
        4. Evite frases promocionais engessadas como “Posso te ajudar a encontrar o modelo perfeito!”. Use linguagem natural, como uma amiga ajudando.
        5. Evite gírias regionais, mas mantenha um tom descontraído.
        6. Ao passar várias informações, evite tanto colocar tudo numa linha só quanto quebrar demais — busque equilíbrio.
        7. Varie cumprimentos e respostas, evitando repetir sempre as mesmas frases.
        8. Nunca use o seguinte caractere: —
        9. Seja direta, não fale coisas desnecessárias, principalmente se forem dúvidas simples.

        # Formatação das respostas #

        A resposta final deve vir separada em mensagens fracionadas, simulando conversa natural.
        O símbolo para separação será: $%&$
        Se houver link, ele deve estar sozinho em uma fração (sem texto antes ou depois).
        Se houver vários links, cada um deve vir em uma fração separada.

        ## Exemplo de saída ##

        Oi!$%&$Tudo bem?$%&$Como posso te ajudar hoje?

        ## Exemplos de conversas reais ##
        Estes exemplos são apenas referência de tom e estilo, não devem ser incluídos nas respostas.

        Cliente: Eu tô procurando um modelo de top mais curtinho, pra usar com camisa.
        Atendente: Temos sim! O top faixa ele é curto e básico.

        Cliente: preciso de 3 shorts iguais para uma corrida no domingo, pra mim e para duas amigas!
        Atendente: Claro!! Me diz o tamanho que vocês vestem que eu te digo o que temos aqui pra vocês.

        Cliente: tem blusa coladinho?
        Atendente: Temos sim! Temos algumas opções de regatas que são de poliamida e ficam bem coladinhas.

        Cliente: O bolso é grande o suficiente para dar um celular, chave e essas coisinhas?
        Atendente: Sim!! Cabe até uma garrafa de água de 500ml.

        """
    
    prompt_template = ChatPromptTemplate(
    input_variables=["history", "current_messages", "sys_prompt"],
    messages=[
        ("system", sys_prompt),
        MessagesPlaceholder(variable_name="history"),
        MessagesPlaceholder(variable_name="current_messages"),
    ],
)

    full_input = {
    "history": history,  # mensagens antigas
    "current_messages": state["messages"],  # mensagens novas
    "sys_prompt": sys_prompt
}

    prompt = prompt_template.invoke(full_input)
    resposta = model.invoke(prompt)
    
    return {"messages": [resposta]}

def vazio(state: AgentState, config: RunnableConfig):
    return {"messages": [AIMessage(content="")]}  # Retorna uma mensagem vazia


def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    
    if not last_message.tool_calls:
        return "formatador"
    else:
        return "no_ferramenta"

def limit_steps(state):
    if state["remaining_steps"] <= 8:
        return "formatador"
    else:
        return "roteador"

    
def save(state, config):
    conversation_id = config.get("configurable", {}).get("conversation_id", "default")
    save_message(conversation_id, state["messages"])


def build_chat_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("roteador", roteador)
    workflow.add_node("formatador", formatador)
    workflow.add_node("no_ferramenta", ToolNode(tools))
    workflow.add_node("save", save)
    workflow.add_node("limitador", limit_steps)

    workflow.add_edge(START, "roteador")
    workflow.add_conditional_edges("roteador", should_continue)
    workflow.add_edge("no_ferramenta", "limitador")
    workflow.add_edge("formatador", "save")
    workflow.add_edge("save", END)

    return workflow.compile()