import os
from .database import get_connection
from flask import session

def get_user_sub():
    """Dynamically fetches the authorized user from the Flask session."""
    try:
        return session.get('user_email', 'guest@local')
    except:
        return 'guest@local'

def save_contacts(contacts):
    # Deprecated for raw dict saving. Used for backward compatibility seeding.
    for name, data in contacts.items():
        if isinstance(data, dict):
            add_contact(name, data.get("email"), data.get("telegram"))
        else:
            add_contact(name, data)

def add_contact(name, email, telegram_username=None, user_sub=None):
    if user_sub is None:
        user_sub = get_user_sub()

    conn = get_connection()
    c = conn.cursor()
    
    # Update if exists, else insert
    c.execute("SELECT id FROM contacts WHERE user_sub=? AND name=?", (user_sub, name.lower()))
    row = c.fetchone()
    if row:
        c.execute("UPDATE contacts SET email=?, telegram_username=? WHERE id=?", 
                 (email.lower(), telegram_username, row[0]))
    else:
        c.execute("INSERT INTO contacts (user_sub, name, email, telegram_username) VALUES (?, ?, ?, ?)",
                 (user_sub, name.lower(), email.lower(), telegram_username))
    conn.commit()
    conn.close()
    return True

def get_email(name, user_sub=None):
    if user_sub is None:
        user_sub = get_user_sub()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT email FROM contacts WHERE user_sub=? AND name=?", (user_sub, name.lower()))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def get_telegram(name, user_sub=None):
    if user_sub is None:
        user_sub = get_user_sub()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT telegram_username FROM contacts WHERE user_sub=? AND name=?", (user_sub, name.lower()))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def delete_contact(name, user_sub=None):
    if user_sub is None:
        user_sub = get_user_sub()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM contacts WHERE user_sub=? AND name=?", (user_sub, name.lower()))
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def update_contact(name, new_email, telegram_username=None, user_sub=None):
    if user_sub is None:
        user_sub = get_user_sub()
    return add_contact(name, new_email, telegram_username, user_sub)

def get_all_contacts(user_sub=None):
    if user_sub is None:
        user_sub = get_user_sub()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name, email, telegram_username FROM contacts WHERE user_sub=?", (user_sub,))
    rows = c.fetchall()
    conn.close()
    
    contacts = {}
    for row in rows:
        contacts[row[0]] = {"email": row[1], "telegram": row[2]}
    return contacts