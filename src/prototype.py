import json

# json file helpers
def load_json(filename):
    with open(filename, "r") as file:
        return json.load(file)

def save_json(filename, data):
    with open(filename, "w") as file:
        return json.load(data, file, indent=4)

def auth(username, password):
    users = load_json("src/users.json")

    # If the username does not exist, will print so
    if username not in users:
        print("\nUsername not found!")
        return False
    
    # If the password matches with the username, returns True and continues the program
    if users[username]["password"] == password:
        print("\nLogin successful!")
        return True
    else:
        print("\nIncorrect password.")
        return False

def signup(username, password):
    users = load_json("src/users.json")

    if username in users:
        print("\nUsername already exist!")
        return False

    # Gets the id before the new user
    if not users: return 1
    highest_id = max(user_id["_id"] for user_id in users.values())

    # Creates the new user
    users[username] = {"_id": highest_id + 1, "password": password}

    save_json("src/users.json", users)
    return True

def main():
    # Login/Signup Sequence
    print("Hello user!\n\n")
    user_choice = input("Would you like to log in or sign-up? (L/S)\n")

    if user_choice == "L":
        username_in = input("\nUsername: ")
        password_in = input("Password: ")
        if auth(username_in, password_in):
            logged_in = True
        else:
            logged_in = False
    
    elif user_choice == "S":
        username_in = input("\nUsername: ")
        password_in = input("Password: ")
        if signup(username_in, password_in):
            logged_in = True
        else:
            logged_in = False
