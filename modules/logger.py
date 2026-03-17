import json
import os
import time

ACTIVITY_FILE = "activity.json"
STATS_FILE = "stats.json"

def load_json(filepath, default):
    if not os.path.exists(filepath):
        return default
    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except:
            return default

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def log_activity(action, user_email):
    logs = load_json(ACTIVITY_FILE, [])
    
    log_entry = {
        "timestamp": time.time(),
        "time_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "user": user_email,
        "action": action
    }
    
    logs.append(log_entry)
    
    # Keep only last 100 logs
    if len(logs) > 100:
        logs = logs[-100:]
        
    save_json(ACTIVITY_FILE, logs)

def increment_emails_sent():
    stats = load_json(STATS_FILE, {"emails_sent": 0})
    stats["emails_sent"] += 1
    save_json(STATS_FILE, stats)

def increment_messages_sent():
    stats = load_json(STATS_FILE, {"messages_sent": 0})
    # If using older stats file, initialize
    if "messages_sent" not in stats:
        stats["messages_sent"] = 0
    stats["messages_sent"] += 1
    save_json(STATS_FILE, stats)

def get_stats():
    stats = load_json(STATS_FILE, {"emails_sent": 0, "messages_sent": 0})
    return stats

def get_recent_logs(limit=20):
    logs = load_json(ACTIVITY_FILE, [])
    return list(reversed(logs))[:limit]
