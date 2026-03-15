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

## HOMEPAGE AUTH
def auth(username, password):
    users = load_json("src/users.json")

    if username not in users:
        print(bcolors.BADRED + "Username or password is incorrect." + bcolors.ENDC)
        return None

    if users[username]["password"] == password:
        print(bcolors.OKGREEN + "Login successful!" + bcolors.ENDC)
        return users[username]["_id"]

    print(bcolors.BADRED + "Incorrect password." + bcolors.ENDC)
    return None

def create_blank_userdata(user_id):
    userdata = load_json("src/userdata.json")

    userdata[str(user_id)] = {
        "quarters": [
            {"quarter": 1, "subjects": []},
            {"quarter": 2, "subjects": []},
            {"quarter": 3, "subjects": []},
            {"quarter": 4, "subjects": []}
        ]
    }

    save_json("src/userdata.json", userdata)

def signup(username, password):
    users = load_json("src/users.json")

    if username in users:
        print(bcolors.BADRED + "Username already exists!" + bcolors.ENDC)
        return None

    if not users:
        new_id = 1
    else:
        highest_id = max(user_data["_id"] for user_data in users.values())
        new_id = highest_id + 1

    users[username] = {"_id": new_id, "password": password}
    save_json("src/users.json", users)
    create_blank_userdata(new_id)

    print(bcolors.OKGREEN + "Signup successful!" + bcolors.ENDC)
    return new_id

def auth_sequence():
    print("Hello user!\n")
    user_choice = input("Would you like to log in or sign-up? (L/S)\n").upper()

    if user_choice == "L":
        while True:
            username_in = input("\nUsername: ")
            password_in = input("Password: ")
            user_id = auth(username_in, password_in)
            if user_id is not None:
                return user_id

    elif user_choice == "S":
        while True:
            username_in = input("\nUsername: ")
            password_in = input("Password: ")
            user_id = signup(username_in, password_in)
            if user_id is not None:
                return user_id

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