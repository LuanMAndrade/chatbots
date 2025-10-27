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
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Annotated, TypedDict, Sequence, List
from pathlib import Path


from graph.nao_entendi import nao_entendi
from graph.informacoes import informacoes
from banco_dados.message_history import save_message, get_history
from django_utils.update_info import fetch_bot_info




LINK_AGENDAMENTO = os.getenv("LINK_AGENDAMENTO")

tools = [nao_entendi]

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
        Você é uma secretária virtual.
        Número de identificação do cliente {conversation_id}

        # Uso das ferramentas #
        Você tem acesso às ferramentas abaixo. Use-as quando necessário para responder a(o) cliente

        <Ferramentas>
        1. nao_entendi - Use quando não entender a solicitação da cliente. Só use como último recurso.
        </Ferramentas>

        # Regras #
        1. Para agendamento o cliente deve usar o seguinte link {LINK_AGENDAMENTO}
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

    model = ChatOpenAI(model="gpt-4.1", temperature=0)

    conversation_id = config.get("configurable", {}).get("conversation_id", "default") ##
    history = get_history(conversation_id) ##
    try:
        BASE_DIR = Path(__file__).resolve().parent.parent
        info_file_path = BASE_DIR / 'data' / 'inf_loja.txt'
        with open(info_file_path, 'r', encoding='utf-8') as f:
            sys_prompt = f.read()
    except FileNotFoundError:
        sys_prompt = "Desculpe, as informações do bot não foram encontradas."
    except Exception as e:
        sys_prompt = f"Ocorreu um erro ao carregar as informações do bot: {e}"
    
    sys_prompt = sys_prompt.replace("{LINK_AGENDAMENTO}", LINK_AGENDAMENTO)
    prompt_template = ChatPromptTemplate(
    input_variables=["history", "current_messages", "sys_prompt"],
    # partial_variables={"format_instructions": parser.get_format_instructions()},
    messages=[
        ("system", sys_prompt),
        MessagesPlaceholder(variable_name="history"),
        MessagesPlaceholder(variable_name="current_messages"),
    ],
)

    full_input = {
        "history": history,
        "current_messages": state["messages"],
    }

    prompt = prompt_template.invoke(full_input)

    resposta = model.invoke(prompt)

    return {"messages": [resposta]}


def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    
    if state["remaining_steps"] <= 8:
        return "no_ferramenta_final"
    elif not last_message.tool_calls:
        return "formatador"
    else:
        return "no_ferramenta"
    
def save(state, config):
    conversation_id = config.get("configurable", {}).get("conversation_id", "default")
    save_message(conversation_id, state["messages"])


def build_chat_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("roteador", roteador)
    workflow.add_node("formatador", formatador)
    workflow.add_node("no_ferramenta", ToolNode(tools))
    workflow.add_node("no_ferramenta_final", ToolNode(tools))
    workflow.add_node("save", save)

    workflow.add_edge(START, "roteador")
    workflow.add_conditional_edges("roteador", should_continue)
    workflow.add_edge("no_ferramenta", "roteador")
    workflow.add_edge("no_ferramenta_final", "formatador")
    workflow.add_edge("formatador", "save")
    workflow.add_edge("save", END)

    return workflow.compile()