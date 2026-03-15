import json
import tkinter as tk
from tkinter import ttk

## HELPERS/EXTRA
# extra text deco
class bcolors:
    ENDC = '\033[0m'
    BADRED = '\033[91m'
    OKGREEN = '\033[92m'

# json file helpers
def load_json(filename):
    with open(filename, "r") as file:
        return json.load(file)

def save_json(filename, data):
    with open(filename, "w") as file:
        return json.dump(data, file, indent=4)

def auth(username, password):
    users = load_json("src/users.json")

    # If the username does not exist, will print so
    if username not in users:
        print(bcolors.BADRED + "Username or password is incorrect." + bcolors.ENDC)
        return False
    
    # If the password matches with the username, returns True and continues the program
    if users[username]["password"] == password:
        print(bcolors.OKGREEN + "Login successful!" + bcolors.ENDC)
        return True
    else:
        print(bcolors.BADRED + "Incorrect password." + bcolors.ENDC)
        return False

## HOMEPAGE AUTH
def signup(username, password):
    users = load_json("src/users.json")

    if username in users:
        print(bcolors.BADRED + "Username already exists!" + bcolors.ENDC)
        return False

    # Gets the id before the new user
    if not users: return 1
    highest_id = max(user_id["_id"] for user_id in users.values())

    # Creates the new user
    users[username] = {"_id": highest_id + 1, "password": password}

    save_json("src/users.json", users)
    print(bcolors.OKGREEN + "Signup successful!" + bcolors.ENDC)
    return True

def auth_sequence():
    # Login/Signup Sequence
    print("Hello user!\n")
    user_choice = input("Would you like to log in or sign-up? (L/S)\n")

    # Self-explanatory
    if user_choice == "L":
        while True:
            username_in = input("\nUsername: ")
            password_in = input("Password: ")
            if auth(username_in, password_in):
                return True
    
    # Self-explanatory
    elif user_choice == "S":
        while True:
            username_in = input("\nUsername: ")
            password_in = input("Password: ")
            if signup(username_in, password_in):
                return True

## GUI WINDOW
def table_ui():
    window = tk.Tk()
    window.title("Report Card Table")
    
    # Everything below except window.mainloop() is from prompting Chat-GPT "how to make table using tkinter python"
    table_frame = tk.Frame(window)
    table_frame.pack(expand=True)

    columns = ("Subject", "Grade", "Unit", "Remarks")

    table = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=8
    )

    for column in columns:
        table.heading(column, text=column)
        table.column(column, anchor="center", width=150)
    
    # sample data
    data = [
        ("Math", "95", "Excellent"),
        ("Science", "89", "Very Good"),
        ("English", "92", "Very Good"),
        ("Filipino", "88", "Good"),
        ("PE", "97", "Outstanding")
    ]

    for row in data:
        table.insert("", tk.END, values=row)

    table.pack()

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    table.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    window.mainloop()

## PROGRAM SEQUENCER
def main():
    if auth_sequence():
        table_ui()

main()