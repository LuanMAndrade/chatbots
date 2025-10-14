from langchain_core.tools import tool
from typing import Annotated
import sqlite3

@tool
def add_to_cart(user_id:Annotated[str, "Número de identificação do usuário"], product_id: Annotated[int, "Número 'id' do produto. Consta nas informações do produto "], quantity: Annotated[int, "Quantidade do produto"]):
    """Adiciona um produto ao carrinho do usuário."""
    conn = sqlite3.connect("data_base.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        product_id INT,
        quantity INT
    )
    """)
    # Verifica se já existe o produto no carrinho
    cur.execute("SELECT quantity FROM cart WHERE user_id=? AND product_id=?", (user_id, product_id))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE cart SET quantity = ? WHERE user_id=? AND product_id=?",
                    (quantity, user_id, product_id))
    else:
        cur.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
                    (user_id, product_id, quantity))
    conn.commit()
    conn.close()
    return f"Produto {product_id} adicionado (qtd {quantity})."


@tool
def remove_from_cart(user_id:Annotated[str, "Número de identificação do usuário"], product_id: Annotated[int, "Número 'id' do produto. Consta nas informações do produto "]):
    """Remove um produto do carrinho do usuário."""
    conn = sqlite3.connect("data_base.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE user_id=? AND product_id=?", (user_id, product_id))
    conn.commit()
    conn.close()
    return f"Produto {product_id} removido do carrinho."


@tool
def view_cart(user_id:Annotated[str, "Número de identificação do usuário"]):
    """Mostra os itens atuais do carrinho do usuário."""
    conn = sqlite3.connect("data_base.db")
    cur = conn.cursor()
    cur.execute("SELECT product_id, quantity FROM cart WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    
    if not rows:
        return "Seu carrinho está vazio."
    carrinho = ""
    for row in rows:
        id = str(row[0])
        print(id)
        cur.execute("SELECT Nome FROM estoque WHERE ID =?", (id,))
        produto = cur.fetchall()
        print(f"!!!!!!!!!!!!!! {produto}", flush= True)
        carrinho += f"Produto: {produto[0][0]}, Quantidade: {row[1]}\n"
    conn.close()
    return carrinho

def remove_from_cart2(user_id:Annotated[str, "Número de identificação do usuário"]):
    """Remove um produto do carrinho do usuário."""
    conn = sqlite3.connect("data_base.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return f"Produto removido do carrinho."