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
    user_data = get_user_data[user_id]
    user_data["subjects"].append(
        {
            "name": name,
            "unit": unit,
            "quarters": [
                {"quarter": 1, "assessments": {}, "grade": None},
                {"quarter": 2, "assessments": {}, "grade": None},
                {"quarter": 3, "assessments": {}, "grade": None},
                {"quarter": 4, "assessments": {}, "grade": None}
            ]
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

def terminal_sequence(user_id):
    print("(Check the windows opened for reference!)")
    report_card_choice = input("Do you want to add a new subject or edit a quarter's assessments? (S/Q)\n").upper()

    if report_card_choice == "S":
        add_new_subject(user_id)

## GUI (WINDOW)
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
    if user_id := auth_sequence():
        terminal_sequence(user_id)

main()