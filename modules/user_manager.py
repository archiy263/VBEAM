import json
import os

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def get_user(email):
    users = load_users()
    email_lower = email.lower()
    
    # If the user doesn't exist, create a default profile with PIN 1234
    if email_lower not in users:
        users[email_lower] = {
            "pin": "1234",
            "role": "admin" if email_lower == "admin@example.com" else "user" 
            # Note: Hardcoding a default admin for demo purposes, but in real life change this.
        }
        save_users(users)
        
    return users.get(email_lower)

def set_user_pin(email, pin):
    users = load_users()
    email_lower = email.lower()
    if email_lower not in users:
        get_user(email_lower) # initialize
        users = load_users()
        
    users[email_lower]["pin"] = str(pin)
    save_users(users)
    return True

def is_admin(email):
    user = get_user(email)
    return user.get("role") == "admin"

def get_total_users():
    return len(load_users())
