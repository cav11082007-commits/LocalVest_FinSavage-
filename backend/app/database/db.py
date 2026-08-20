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

def migrate_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Check if 'images' column exists in 'projects' table
    cur.execute("PRAGMA table_info(projects)")
    columns = [info['name'] for info in cur.fetchall()]
    if 'images' not in columns:
        try:
            cur.execute("ALTER TABLE projects ADD COLUMN images TEXT DEFAULT '[]'")
            conn.commit()
        except sqlite3.OperationalError:
            pass
            
    # Check if 'dob' column exists in 'kyc_documents' table
    cur.execute("PRAGMA table_info(kyc_documents)")
    kyc_columns = [info['name'] for info in cur.fetchall()]
    if 'dob' not in kyc_columns:
        try:
            cur.execute("ALTER TABLE kyc_documents ADD COLUMN dob TEXT")
            cur.execute("ALTER TABLE kyc_documents ADD COLUMN current_address TEXT")
            cur.execute("ALTER TABLE kyc_documents ADD COLUMN social_link TEXT")
            cur.execute("ALTER TABLE kyc_documents ADD COLUMN bank_info TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass
            
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
else:
    migrate_db()
