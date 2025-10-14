from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from typing import Annotated
import json
from langchain_google_genai import ChatGoogleGenerativeAI

from data_base.produtos import busca_atributos
from data_base.qdrant import chama_qdrant

if __name__ == "__main__":
    query = "https://sejasuamodafit.com.br/wp-content/uploads/2024/06/8.png"
    if query.startswith("http"):
        vectorstore = chama_qdrant("estoque_vetorial")
        response = vectorstore.similarity_search(
            query="",
            filter={
                "must": [
                    {
                        "key": "Cor",
                        "match": {
                            "text": "vinho"
                        }
                    }
                ]
            },
            k=2
        )
        print(response) 