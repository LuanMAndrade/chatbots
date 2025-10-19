import sqlite3
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import json

def init_db():
    conn = sqlite3.connect("data/data_base.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT,
        role TEXT, -- 'human' ou 'ai'
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def save_message(conversation_id, messages):
    
    conn = sqlite3.connect("data/data_base.db")
    c = conn.cursor()

    input = str(messages[0].content)
    role = "human"
    c.execute("""
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
        """, (conversation_id, role, input))
    output = str(messages[-1].content)
    role = "ai"
    c.execute("""
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
        """, (conversation_id, role, output))

    c.execute("""
            DELETE FROM messages
            WHERE conversation_id = ?
            AND id NOT IN (
            SELECT id FROM (
            SELECT id
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT 10
        )
    )
""", (conversation_id, conversation_id))

    conn.commit()
    conn.close()



def get_history(conversation_id):

    conn = sqlite3.connect("data/data_base.db")
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id",
              (conversation_id,))
    rows = c.fetchall()
    conn.close()

    history = []
    for role, content_str in rows:
        if role == "human":
            history.append(HumanMessage(content=content_str))
        elif role == "tool":
            data = json.loads(content_str)
            history.append(AIMessage(content=data["content"]))
        elif role == "ai":
            history.append(AIMessage(content=content_str))
        else:
            history.append(HumanMessage(content=content_str))
    return history