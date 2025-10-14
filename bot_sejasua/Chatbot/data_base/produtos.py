import sqlite3


def busca_db():
    conn = sqlite3.connect("data_base.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
    Nome,
    Categorias,
    "Nome do atributo 1", 
    "Valores do atributo 1", 
    "Nome do atributo 2", 
    "Valores do atributo 2",
    TIPO            
    FROM estoque
    """)
    return cursor.fetchall()

def busca_atributos():
    linhas = busca_db()
    cores = []
    tamanhos = []
    categorias = []
    nomes = []
    for nome, categoria, nome_do_atributo_1, valores_do_atributo_1, nome_do_atributo_2, valores_do_atributo_2, tipo in linhas:
        
        if tipo == "variable":
            nome = nome.lower().strip().split()
            nome = " ".join(nome[1:])
            if categoria:
                categoria = categoria.lower()
            if nome not in nomes:
                nomes.append(nome)
            if categoria not in categorias:
                categorias.append(categoria)

        if tipo == "variation":
            dicionario = {nome_do_atributo_1:valores_do_atributo_1.lower() if valores_do_atributo_1 else None, nome_do_atributo_2:valores_do_atributo_2.lower() if valores_do_atributo_2 else None}
            if dicionario.get("Cor"):
                cor = dicionario.get("Cor")
            if dicionario.get("Tamanho"): 
                tamanho = dicionario.get("Tamanho")

            if cor not in cores:
                cores.append(cor)
            if tamanho not in tamanhos:    
                tamanhos.append(tamanho)

    return nomes, categorias, cores, tamanhos
        