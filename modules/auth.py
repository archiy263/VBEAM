import sqlite3
import hashlib
from modules.database import get_connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, name, password):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)", 
                  (email, name, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(email, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT email, name, is_blocked FROM users WHERE email = ? AND password_hash = ?", 
              (email, hash_password(password)))
    user = c.fetchone()
    conn.close()
    if user:
        if user[2] == 1:
            return {"error": "Account blocked"}
        return {"email": user[0], "name": user[1]}
    return None

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, email, name, auth_provider, is_blocked FROM users")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "email": r[1], "name": r[2], "auth_provider": r[3], "is_blocked": bool(r[4])} for r in rows]

def get_or_create_google_user(email, name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT email, name, is_blocked FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    
    if user:
        conn.close()
        if user[2] == 1:
            return {"error": "Account blocked"}
        return {"email": user[0], "name": user[1]}
        
    try:
        c.execute("INSERT INTO users (email, name, password_hash, auth_provider) VALUES (?, ?, ?, ?)", 
                  (email, name, "oauth2", "google"))
        conn.commit()
        return {"email": email, "name": name}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def toggle_block_user(email, block_status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET is_blocked = ? WHERE email = ?", (1 if block_status else 0, email))
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def delete_user(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE email = ?", (email,))
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def update_user(current_email, new_name, new_email):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET name = ?, email = ? WHERE email = ?", 
                  (new_name, new_email, current_email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
