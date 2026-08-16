import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'localvest.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'sqlite_schema.sql')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

def is_db_empty():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()
    return count == 0

# Khởi tạo DB nếu chưa có
if not os.path.exists(DB_PATH):
    init_db()
