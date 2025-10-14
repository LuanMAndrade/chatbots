from langchain_core.tools import tool
from langchain_community.document_loaders import TextLoader
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
documento = BASE_DIR/'data/inf_loja.txt'
informacoes = TextLoader(documento, encoding='utf-8').load()[0].page_content


@tool
def informacoes():
    """Retorna sobre a Loja, mas não sobre os produtos. São informações gerais, do tipo: endereço, telefone, horário de funcionamento."""
    return informacoes