import sqlite3
import pandas as pd
from pathlib import Path
from qdrant_client import QdrantClient

from data_base.qdrant import cria_colecao

def cria_estoque():
    BASE_DIR = Path(__file__).resolve().parent.parent
    documento = BASE_DIR/'data/estoque.csv'

    df = pd.read_csv(documento)
    df.sort_values(by="Nome")
    df = df.get(["ID", "Tipo", "Nome", "Categorias", "Nome do atributo 1", "Valores do atributo 1", "Nome do atributo 2", "Valores do atributo 2", "Descrição curta", "Preço", "Em estoque?", "Estoque", "Metadado: rtwpvg_images", "Imagens", "Ascendente","SKU"])
    df['Nome do atributo 2'].fillna('Tamanho', inplace=True)
    df['Valores do atributo 2'].fillna('único', inplace=True)

    for index, row in df.iterrows():
        df.loc[index, "Valores do atributo 1"] = df.loc[index, "Valores do atributo 1"].lower()
        df.loc[index, "Valores do atributo 2"] = df.loc[index, "Valores do atributo 2"].lower()
        df.loc[index, "Nome"] = df.loc[index, "Nome"].lower()

        if row["Nome do atributo 1"] == "Tamanho":
            df.loc[index, "Nome do atributo 1"] = "Cor"
            df.loc[index, "Nome do atributo 2"] = "Tamanho"
            x = df.loc[index, "Valores do atributo 1"]
            df.loc[index, "Valores do atributo 1"] = df.loc[index, "Valores do atributo 2"]
            df.loc[index, "Valores do atributo 2"] = x

        if row["Tipo"] == "variation":
            ascendente = row["Ascendente"]
            df.loc[index, "Descrição curta"] = df.loc[df["SKU"] == ascendente, "Descrição curta"].values[0]
            categoria = df.loc[df["SKU"] == ascendente, "Categorias"].values[0].lower()
            df.loc[index, "Categorias"] = categoria.split(">")[0].strip()

    for index, row in df.iterrows():
        if row["Tipo"] == "variable":
            sku = row["SKU"]
            df.loc[index, "Preço"] = df.loc[df["Ascendente"] == sku, "Preço"].values[0]
            df.loc[index, "Categorias"] = df.loc[index, "Categorias"].lower().split(">")[0].strip()

    conn = sqlite3.connect("data_base.db")

    df.to_sql("estoque", conn, if_exists="replace", index=False)

    conn.close()

if __name__ == '__main__':
    cria_estoque()
    client = QdrantClient(url=QDRANT_URL)
    client.delete_collection("estoque_vetorial")
    cria_colecao("estoque_vetorial")