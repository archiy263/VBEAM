import os
import sqlite3

DB_FILE = "app_data.db"
# Render injects DATABASE_URL for Postgres databases automatically
DATABASE_URL = os.environ.get("DATABASE_URL")
DB_TYPE = "postgres" if DATABASE_URL else "sqlite"

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DB_TYPE == "postgres":
    import psycopg2
    from psycopg2.extras import DictCursor

    class CursorWrapper:
        def __init__(self, cursor):
            self.cursor = cursor
        
        def execute(self, query, params=None):
            # Translate common SQLite constructs to Postgres
            pg_query = query.replace("?", "%s")
            pg_query = pg_query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            pg_query = pg_query.replace("DATETIME", "TIMESTAMP")
            pg_query = pg_query.replace("BLOB", "BYTEA")
            
            try:
                if params:
                    self.cursor.execute(pg_query, params)
                else:
                    self.cursor.execute(pg_query)
            except Exception as e:
                # If column duplicate error during migrations, ignore
                if "already exists" in str(e):
                    pass
                else:
                    raise e
            return self

        def fetchone(self): return self.cursor.fetchone()
        def fetchall(self): return self.cursor.fetchall()
        @property
        def rowcount(self): return self.cursor.rowcount
        def close(self): self.cursor.close()

    class ConnectionWrapper:
        def __init__(self, conn):
            self.conn = conn
        def cursor(self):
            return CursorWrapper(self.conn.cursor())
        def commit(self): self.conn.commit()
        def close(self): self.conn.close()

def get_connection():
    if DB_TYPE == "postgres":
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return ConnectionWrapper(conn)
    else:
        return sqlite3.connect("app_data.db")

def add_column(cursor, conn_obj, stmt):
    try:
        cursor.execute(stmt)
        conn_obj.commit()
    except Exception as e:
        if DB_TYPE == "postgres":
            # Postgres transactions must be rolled back on failed query
            conn_obj.conn.rollback()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Create Contacts Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_sub TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            telegram_username TEXT
        )
    ''')
    conn.commit()
    
    # Create Users Table for manual auth
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    
    add_column(c, conn, "ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'manual'")
    add_column(c, conn, "ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")
    add_column(c, conn, "ALTER TABLE users ADD COLUMN pin TEXT DEFAULT '1234'")
    add_column(c, conn, "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    add_column(c, conn, "ALTER TABLE users ADD COLUMN google_token BLOB")

    # Create Activity Logs Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_sub TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    # Create Active User Tracking Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT UNIQUE NOT NULL,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

# Initialize schema definitions on load
init_db()
