import sqlite3

async def salva_id_imagem(sender, id, link):
    conn = sqlite3.connect("data_base.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS images_id (
        id TEXT,
        image_id TEXT,
        link TEXT
    )
    """)
    c.execute("""
            INSERT INTO images_id (id, image_id, link)
            VALUES (?, ?, ?)
        """, (sender, id, link))
    conn.commit()
    conn.close()
    print("Salvei", flush=True)
    return "ok"

async def busca_imagem(id):
    conn = sqlite3.connect("data_base.db")
    c = conn.cursor()
    c.execute("""
        SELECT link FROM images_id WHERE image_id = ?
    """, (id,))
    result = c.fetchone()
    conn.close()
    print(f"RESULTADO {result}", flush=True)
    return result