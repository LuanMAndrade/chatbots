import os
import sqlite3
from dotenv import load_dotenv
from data_base.qdrant import cria_colecao
from qdrant_client import QdrantClient


load_dotenv()

SERVER_IP = os.getenv("SERVER_IP")
QDRANT_URL_TEMPLATE = os.getenv("QDRANT_URL")
QDRANT_URL = QDRANT_URL_TEMPLATE.format(SERVER_IP=SERVER_IP)


async def woocommerce(data):
    id = data.get("id")
    nome = data.get("name")
    tipo = data.get("type")
    preco = data.get("price")
    estoque = data.get("stock_quantity")
    tamanho = None
    cor = None
    em_estoque = data.get("stock_status")
    em_estoque = 1 if em_estoque == "instock" else 0
    for item in data["attributes"]:
        if item["name"] == "Tamanho":
            tamanho = item.get("option")
        if item["name"] == "Cor":
            cor = item.get("option")
    imagem = data.get("src")
    descricao =data.get("short_description")
    print(f"ID: {id}, Nome: {nome} Tipo: {tipo}, Preço: {preco}, Estoque: {estoque}, Tamanho: {tamanho}, Cor: {cor}, Imagem: {imagem}, Descrição: {descricao}, ")

    conn = sqlite3.connect('data_base.db')
    cursor = conn.cursor()

    if tipo == "variable":
        cursor.execute("""UPDATE estoque SET Estoque = ?, Preço = ?, "Valores do atributo 1" = ?, "Valores do atributo 2" = ?, "Descrição curta"= ?, Imagens = ?, "Em estoque?" = ?  WHERE id = ? """, (estoque, preco, cor, tamanho, descricao, imagem, em_estoque, id)) 
    else:
        cursor.execute("""UPDATE estoque SET Estoque = ?, Preço = ?, "Metadado: rtwpvg_images" = ?,  "Em estoque?" = ?  WHERE id = ? """, (estoque, preco, imagem, em_estoque, id)) 
    conn.commit()
    conn.close()
    client = QdrantClient(url=QDRANT_URL)
    client.delete_collection("estoque_vetorial")
    cria_colecao("estoque_vetorial")

    return {"ok": True}