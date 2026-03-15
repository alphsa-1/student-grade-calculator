import json

with open("users.json", "r") as f:
    users = json.load(f)

def auth(username, password):
    global users
    if username not in users:
        return 0
    
    if users[username]["password"] == password:
        return 2
    else:
        return 1