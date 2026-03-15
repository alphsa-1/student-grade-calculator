import json

with open("src/users.json", "r") as f:
    users = json.load(f)

def message(auth_val):
    match auth_val:
        case 0: print("Username not found!")
        case 1: print("Incorrect password.")
        case 2: print("Login successful!")

def auth(username, password):
    global users
    if username not in users:
        message(0)
        return False
    
    if users[username]["password"] == password:
        message(2)
        return True
    else:
        message(1)
        return False
    
auth("john", "pass123")