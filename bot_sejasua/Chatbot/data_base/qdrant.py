from langchain_qdrant import QdrantVectorStore
from langchain_openai.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
import os
import sqlite3
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import json
from qdrant_client import QdrantClient
import pandas as pd

load_dotenv()


SERVER_IP = os.getenv("SERVER_IP")
QDRANT_URL_TEMPLATE = os.getenv("QDRANT_URL")
QDRANT_URL = QDRANT_URL_TEMPLATE.format(SERVER_IP=SERVER_IP)

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


def busca_db():
    conn = sqlite3.connect("data_base.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
    ID,
    Nome,
    Categorias,
    "Valores do atributo 1", 
    "Valores do atributo 2",               
    "Descrição curta", 
    Preço, 
    Estoque,
    "Metadado: rtwpvg_images",
    Imagens,
    Tipo
    FROM estoque

    """)
    print("Buscou no banco de dados de estoque")
    return cursor.fetchall()

def cria_documento():
    conn = sqlite3.connect("data_base.db")
    df = pd.read_sql_query("""
    SELECT 
    ID,
    Nome,
    Categorias,
    Preço,
    "Metadado: rtwpvg_images",
    Imagens,
    "Descrição curta",
    Ascendente,
    SKU,
    Estoque,
    "Valores do atributo 1", 
    "Valores do atributo 2",
    Tipo            
    FROM estoque
    """, conn)

    documentos = []
    for index, row in df.iterrows():
        if row["Tipo"] == "variable":
                sku = row["SKU"]
                cores = df.loc[df["Ascendente"] == sku, "Valores do atributo 1"].values
                tamanhos = df.loc[df["Ascendente"] == sku, "Valores do atributo 2"].values
                estoques = df.loc[df["Ascendente"] == sku, "Estoque"].values
                descricao = str(row["Descrição curta"]) + "\nOutras variações deste produto:"
                for cor, tamanho, estoque in zip(cores, tamanhos, estoques):
                    descricao += "\nCor: " +str(cor.strip()) +", Tamanho: " + str(tamanho.strip()) + ", Estoque: " + str(estoque)
                df.loc[index, "Descrição curta"] = descricao

    for index, row in df.iterrows():
        if row["Tipo"] == "variation":
            ascendente = row["Ascendente"]
            row["Descrição curta"] = df.loc[df["SKU"] == ascendente, "Descrição curta"].values[0]

        descricao = row["Descrição curta"]
        id_ = row["ID"]
        nome = row["Nome"]
        categoria = row["Categorias"]
        valores_do_atributo_1 = row["Valores do atributo 1"]
        valores_do_atributo_2 = row["Valores do atributo 2"]
        preco = row["Preço"]
        estoque = row["Estoque"]
        imagens = row["Metadado: rtwpvg_images"]
        tipo = row["Tipo"]
        documento_atual = Document(page_content=json.dumps(descricao, ensure_ascii=False), metadata={"id": id_,'Tipo': tipo, 'Nome': nome, 'Categoria': categoria, "Cor": valores_do_atributo_1, "Tamanho": valores_do_atributo_2, 'Estoque': estoque, 'Preço': preco, 'Links_das_imagens': imagens})
        documentos.append(documento_atual)

    return documentos

# def cria_documento(linhas):
#     documentos = []
#     for id_, nome, categoria, valores_do_atributo_1, valores_do_atributo_2, descricao, preco, estoque, imagens, imagem_principal, tipo in linhas:
#             documento_atual = Document(page_content=json.dumps(descricao, ensure_ascii=False), metadata={"id": id_,'Tipo': tipo, 'Nome': nome, 'Categoria': categoria, "Cor": valores_do_atributo_1, "Tamanho": valores_do_atributo_2, 'Estoque': estoque, 'Preço': preco, 'Links_das_imagens': imagens})
#             documentos.append(documento_atual)
#     print("Criou docs")
    
#     return documentos

def cria_colecao(nome_colecao: str):
    linhas = busca_db()
    documentos = cria_documento()
    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    QdrantVectorStore.from_documents(
        documents=documentos,
        embedding=embedding_model,
        url=QDRANT_URL,
        collection_name=nome_colecao,
    )
    print("Coleção criada com sucesso!")

def chama_qdrant(nome_colecao: str):
    try:
        db = QdrantVectorStore.from_existing_collection(
            collection_name=nome_colecao,
            url= QDRANT_URL,
            embedding=OpenAIEmbeddings(model=EMBEDDING_MODEL),
        )
    except Exception as e:
        print(f"Erro ao conectar com Qdrant: {e}")
        return None
    return db

if __name__ == "__main__":
    client = QdrantClient(url=QDRANT_URL)
    client.delete_collection("estoque_vetorial")
    cria_colecao("estoque_vetorial")