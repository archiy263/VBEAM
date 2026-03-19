import sqlite3
from modules.database import get_connection

def get_user(email):
    """Retrieve user PIN and Role from the robust SQLite database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT pin, role FROM users WHERE email = ?", (email.lower(),))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {"pin": row[0], "role": row[1]}
    
    # Fallback default if user row isn't found
    return {"pin": "1234", "role": "user"}

def set_user_pin(email, pin):
    """Save the custom 4-digit Voice PIN to the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET pin = ? WHERE email = ?", (str(pin), email.lower()))
    conn.commit()
    conn.close()
    return True

def set_user_role(email, role):
    """Manually escalate or modify a user's role."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET role = ? WHERE email = ?", (role, email.lower()))
    conn.commit()
    conn.close()
    return True

def is_admin(email):
    """Check if a given email is granted 'admin' status."""
    if not email:
        return False
        
    email_lower = email.lower()
    
    # Hardcoded root super-admin so you never lose control
    if email_lower == "archiyadav262003@gmail.com":
        return True
        
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE email = ?", (email_lower,))
    row = c.fetchone()
    conn.close()
    
    if row and row[0] == "admin":
        return True
    return False

def get_total_users():
    """Counts total registered users across all auth methods."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(id) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def update_activity(email):
    """Upsert activity timestamp for a user. Marks them active."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_activity (user_email, last_seen, is_active)
        VALUES (?, CURRENT_TIMESTAMP, 1)
        ON CONFLICT(user_email) DO UPDATE SET 
        last_seen=CURRENT_TIMESTAMP, is_active=1
    """, (email.lower(),))
    conn.commit()
    conn.close()

def get_active_users(timeout_minutes=10):
    """Retrieve users seen within the last N minutes using julianday to track precise sessions."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT user_email, last_seen FROM user_activity 
        WHERE (julianday('now') - julianday(last_seen)) * 1440 <= ? 
        AND is_active=1
        ORDER BY last_seen DESC
    """, (timeout_minutes,))
    rows = c.fetchall()
    conn.close()
    return [{"email": r[0], "last_seen": r[1]} for r in rows]
