from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from typing import Annotated
import json
from langchain_google_genai import ChatGoogleGenerativeAI

from data_base.produtos import busca_atributos
from data_base.qdrant import chama_qdrant


nomes, categorias, cores, tamanhos = busca_atributos()

@tool
def rag(query: Annotated[str, "Utiliza a query da cliente para buscar produtos relevantes no estoque."]):
    """Realiza uma busca híbrida, utilizando busca direta e busca por contexto. Retorna os produtos mais relevantes de acordo com a demanda da cliente.""" 
    llm = ChatOpenAI(model="gpt-5-mini")
    vectorstore = chama_qdrant("estoque_vetorial")
    metadata_field_info = [
        AttributeInfo(
            name="Cor",
            description=f"Cor do produto. Um dentre estes: {cores} Use sempre busca parcial (contém) para este campo. Quando a cor possuir variações de escrita, por exemplo, amarelo e amarela, busque pelo radical da palavra (contém) 'amarel'. Sempre em lowercase ",
            type="string",
        ),
        AttributeInfo(
            name="Tamanho",
            description=f"Tamanho do produto. Um dentre estes: p, m, g, único. Sempre em lowercase",
            type="string",
        ),
        AttributeInfo(
            name="Preço",
            description="Preço do produto",
            type="integer",
        ),
        AttributeInfo(
            name="id",
            description="ID do produto",
            type="integer",
        ),
        AttributeInfo(
            name="Nome",
            description=f"Nome do produto. Um dentre estes: {nomes}. Use sempre busca parcial (contém) para este campo. Sempre em lowercase ",
            type="string",
        ),
        AttributeInfo(
            name="Tipo",
            description="Tipo do produto: variation ou variable",
            type="string",
        ),
        AttributeInfo(
            name="Links_das_imagens",
            description="link da imagem do produto. Se a query for um link, sempre procure por este filtro. Use sempre busca parcial (contém) para este campo.",
            type="string",
        ),
        AttributeInfo(
            name="Estoque",
            description="Quantidade em estoque do produto. Sempre filtre por maior que 0, a não ser que alguém fale o nome específico de um produto",
            type="integer",
        ),
        AttributeInfo(
            name="Categoria",
            description=f"Categoria do produto. Um dentre esses: {categorias}. Biquinis, maiôs e peças semelhantes são considerados moda praia. Sempre em lowercase. Se a query for semelhante a algum desses nomes, atribua a ele. Por exemplo: top -> top's, short -> shorts",
            type="string",
        ),
    ]

    document_content_description = "Breve descrição do produto"
    retriever = SelfQueryRetriever.from_llm(
        llm,
        vectorstore,
        document_content_description,
        metadata_field_info,
        k = 2
    )
    
    response = retriever.invoke(query)

    
    lista_respostas = []

    for doc in response:
        metadados = doc.metadata
        descricao = json.loads(doc.page_content)
        resposta = f"id: {metadados.get("id")}, Nome: {metadados.get("Nome")}\n'Categoria': {metadados.get("Categoria")}, Tamanho: {metadados.get('Tamanho')} Cor: {metadados.get("Cor")}, Estoque: {metadados.get("Estoque")}, Links das imagens:{metadados.get("Links das imagens")} Preço: {metadados.get("Preço")}\nDescrição: {descricao}"
        lista_respostas.append(resposta)
        print(resposta)


    return lista_respostas