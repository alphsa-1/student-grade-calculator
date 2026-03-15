import json
import tkinter as tk
from tkinter import ttk
import threading

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
        print(bcolors.OKGREEN + "Login successful!\n" + bcolors.ENDC)
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

    print(bcolors.OKGREEN + "Signup successful!\n" + bcolors.ENDC)
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

## DATA PARSERS
# helpers
def get_user_data(user_id):
    userdata = load_json("src/userdata.json")
    return userdata.get(str(user_id))

def save_user_data(user_id, user_data):
    userdata = load_json("src/userdata.json")
    userdata[str(user_id)] = user_data
    save_json("src/userdata.json", userdata)

def get_quarter(user_data, quarter_number):
    for quarter in user_data["quarters"]:
        if quarter["quarter"] == quarter_number:
            return quarter
    return None

def create_blank_user_data(user_id):
    return {
        str(user_id): {
            "subjects": []
        }
    }

def create_subject(user_id, name, unit):
    user_data = get_user_data(user_id)
    user_data["subjects"].append(
        {
            "name": name,
            "unit": unit,
            "quarters": [
                {"quarter": 1, "assessments": {}, "grade": None},
                {"quarter": 2, "assessments": {}, "grade": None},
                {"quarter": 3, "assessments": {}, "grade": None},
                {"quarter": 4, "assessments": {}, "grade": None}
            ],
            "final": None,
            "classification": None
        }
    )
    save_user_data(user_id, user_data)

def is_subject_new(subject_name, user_id):
    if any(subject_name == subject["name"] for subject in get_user_data(user_id)["subjects"]):
        return False
    else:
        return True

# main

## GUI (TERMINAL)
def add_new_subject(user_id):
    subject_name = input("Subject name: ")
    subject_unit = float(input("Subject unit: "))
    if not is_subject_new(subject_name, user_id):
        terminal_sequence(user_id)
    else:
        print(bcolors.OKGREEN + "Subject successfully added!" + bcolors.ENDC)
        create_subject(user_id, subject_name, subject_unit)
        # refresh_gui()

def terminal_sequence(user_id, window, table):
    while True:
        print("(Check the window for reference!)")
        choice = input("Do you want to add a new subject or edit a quarter's assessments? (S/Q/X)\n").upper()

        if choice == "S":
            add_new_subject(user_id)
            window.after(0, lambda: refresh_table(user_id, table))

        elif choice == "Q":
            pass

        elif choice == "X":
            window.after(0, window.destroy)
            break

## GUI (WINDOW)
def refresh_table(user_id, table):
    for row in table.get_children():
        table.delete(row)
    
    user_data = get_user_data(user_id)
    for subject in user_data["subjects"]:
        name = subject["name"]
        unit = subject["unit"]
        grades = [quarter["grade"] for quarter in subject["quarters"]]
        final = subject["final"]
        classification = subject["classification"]
        row_data = grades.insert(0, name).append(final, unit, classification)
        table.insert("", tk.END, values=row_data)


def build_table(window):
    table_frame = tk.Frame(window)
    table_frame.pack(expand=True)

    columns = ("Subject", "Q1", "Q2", "Q3", "Q4", "Final", "Unit", "Classification")

    table = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=8
    )

    for column in columns:
        table.heading(column, text=column)
        if len(column) > 2:
            table.column(column, anchor="center", width=200)
        else:
            table.column(column, anchor="center", width=50)
    
    table.pack()
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    table.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    return table

## PROGRAM SEQUENCER
def sequence(user_id):
    # Prompted GPT on how to multi-thread tk window and terminal interaction
    window = tk.Tk()
    window.title("Report Card Table")
    table = build_table(window)

    terminal_thread = threading.Thread(
        target=terminal_sequence,
        args=(user_id, window, table),
        daemon=True
    )
    terminal_thread.start()

    window.mainloop()
def main():
    if user_id := auth_sequence():
        sequence(user_id)

main()