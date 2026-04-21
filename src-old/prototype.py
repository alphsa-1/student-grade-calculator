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
    SPLITCAT = '\033[93m'
    SUBCAT = '\033[94m'
    ASSESS = '\033[96m'

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
    global window
    user_data = get_user_data(user_id)
    for subject in user_data["subjects"]:
        if name == subject["name"]:
            print(bcolors.BADRED + "Subject already exists!" + bcolors.ENDC)
            terminal_sequence(user_id, window)

    user_data["subjects"].append(
        {
            "name": name,
            "unit": unit,
            "quarters": [
                {"quarter": i + 1, "assessments": {"SA": {"percentage": None, "categories": []},
                                                   "FA": {"percentage": None, "categories": []}
                                                   }, "grade": None, "passed": None}
                for i in range(4)
            ],
            "final": None,
            "classification": None
        }
    )
    save_user_data(user_id, user_data)

def create_category(user_id, subject_name, quarter, top_level_category, label, percentage):   
    quarter_data = get_quarter_data(user_id, quarter)
    
    for subject in quarter_data:
        if subject[subject_name] is not None:
            subject_data = subject[subject_name]
            break
    else:
        print(bcolors.BADRED + "Subject not found!" + bcolors.ENDC)
        quarter_window.after(0, quarter_window.destroy)
        view_quarter(user_id)
    
    sub_categories = subject_data["assessments"][top_level_category]["categories"]
    sub_categories.append({"label": label, "percentage": percentage, "assessments": []})
    
    save_quarter_data(user_id, quarter, quarter_data)

def create_assessment(user_id, subject_name, quarter, top_level_category, sub_category_name, label, score_obtained, maximum_score):
    quarter_data = get_quarter_data(user_id, quarter)

    for subject in quarter_data:
        if subject[subject_name] is not None:
            subject_data = subject[subject_name]
            break
    else:
        print(bcolors.BADRED + "Subject not found!" + bcolors.ENDC)
        assessments_view(user_id, quarter, subject_name)

    sub_categories = subject_data["assessments"][top_level_category]["categories"]
    for sub_category in sub_categories:
        if sub_category["label"] == sub_category_name:
            sub_category_data = sub_category
            break
    else:
        print(bcolors.BADRED + "Sub-category not found!" + bcolors.ENDC)
        assessments_view(user_id, quarter, subject_name)
    
    sub_category_data["assessments"].append({"label": label, "score_obtained": score_obtained, "maximum_score": maximum_score})
    save_quarter_data(user_id, quarter, quarter_data)

def is_subject_new(subject_name, user_id):
    if any(subject_name == subject["name"] for subject in get_user_data(user_id)["subjects"]):
        return False
    else:
        return True

# main
def get_quarter_data(user_id, quarter):
    user_data = get_user_data(user_id)

    subjects = []
    for subject in user_data["subjects"]:
        formatted = {subject["name"]:  subject["quarters"][quarter - 1]}
        subjects.append(formatted)
    
    return subjects

def save_quarter_data(user_id, quarter, quarter_data):
    user_data = get_user_data(user_id)

    for subject, q_data in zip(sorted(user_data["subjects"], key=lambda x: x["name"]), quarter_data):
        subject["quarters"][quarter - 1] = q_data[subject["name"]]
    
    save_user_data(user_id, user_data)

## GUI (TERMINAL)
def add_new_subject(user_id):
    global window
    subject_name = input("Subject name: ").title()
    subject_unit = float(input("Subject unit: "))
    if not is_subject_new(subject_name, user_id):
        terminal_sequence(user_id, window)
    else:
        print(bcolors.OKGREEN + "Subject successfully added!" + bcolors.ENDC)
        create_subject(user_id, subject_name, subject_unit)
        refresh_table(user_id)

def view_quarter(user_id):
    quarter_choice = int(input("Which quarter do you want to view? (1/2/3/4)\n"))
    global window
    quarter_table_window()
    refresh_quarter_table(user_id, quarter_choice)
    first_choice = input("\nWould you like to edit a subject's assessments? (P [PICK]/B [BACK])\n").upper()
    if first_choice == "B":
        quarter_window.after(0, quarter_window.destroy)
        terminal_sequence(user_id, window)

    if first_choice == "P":
        while True:
            subject_choice = input("\nWhich subject do you want to edit?\n").title()
        
            if subject_choice not in [subject["name"] for subject in get_user_data(user_id)["subjects"]]:
                print(bcolors.BADRED + "Subject not found!" + bcolors.ENDC)
                return_choice = input("\nReturn to homepage? (Y/N)\n").upper()
                if return_choice == "Y":
                    quarter_window.after(0, quarter_window.destroy)
                    terminal_sequence(user_id, window)
                else:
                    print("/n")
                    continue
            else:
                assessments_view(user_id, quarter_choice, subject_choice)

def display_assessments(assessments):
    print("")
    for category in assessments.keys():
        top_level = assessments[category]
        print(bcolors.SPLITCAT + f"Category {category}: " + bcolors.ENDC)
        print(f"Percentage: {top_level['percentage'] if top_level['percentage'] is not None else '* required'}")
        print(f"Sub-categories:\n")

        sub_categories = top_level["categories"]
        for sub_category in sub_categories:
            print(bcolors.SUBCAT + f"Sub-category {sub_category['label']}:" + bcolors.ENDC)
            print(f"Percentage: {sub_category['percentage']}")
            print(f"Assessments:\n")

            for assessment in sub_category["assessments"]:
                print(bcolors.ASSESS + f"Assessment {assessment['label']}: " + bcolors.ENDC)
                print(f"Score Obtained: {assessment['score_obtained']}")
                print(f"Maximum Score: {assessment['maximum_score']}\n")

def assessments_view(user_id, quarter, subject_name):
    global window, quarter_table_window
    quarter_data = get_quarter_data(user_id, quarter)
    for subject in quarter_data:
        if subject[subject_name] is not None:
            subject_data = subject[subject_name]
            break
    else:
        print(bcolors.BADRED + "Subject not found!" + bcolors.ENDC)
        quarter_window.after(0, quarter_window.destroy)
        view_quarter(user_id)

    assessments = subject_data["assessments"]
    display_assessments(assessments)

    def percentage_prompt(category_choice, sub_category_choice = None):
        split_category = 'SA' if category_choice == 'S' else 'FA'
        if sub_category_choice is not None:
            percentage = float(input(f"Enter new percentage for {sub_category_choice} under {category_choice} (0.01 to 1.00): "))
            for category in assessments[split_category]["categories"]:
                if sub_category := category[sub_category_choice] is not None:
                    sub_category["percentage"] = percentage
                    break
            else:
                print(bcolors.BADRED + "Subject not found!" + bcolors.ENDC)
                assessments_view(user_id, quarter, subject_name)

        else:
            percentage = float(input(f"Enter new percentage for {category_choice} (0.01 to 1.00): "))
            assessments[split_category]["percentage"] = percentage
        save_quarter_data(user_id, quarter, quarter_data)
        display_assessments(assessments)
        assessments_view(user_id, quarter, subject_name)

    def assessment_choice():
        choice = input("Would you like to edit a value or add an assessment? (E [EDIT]/ A [ADD]/B [BACK])\n").upper()
        if choice == 'B':
            terminal_sequence(user_id, window)
        elif choice == 'A' or choice == "E":
            top_level_choice(choice)

    def top_level_choice(choice):
        if choice == 'E':
            category_choice = input("\nWhich category would you like to edit? (S [SA]/ F [FA])\n").upper()
        elif choice == 'A':
            category_choice = input("\nWhich category would you like to add to? (S [SA]/ F [FA])\n").upper()
        category_options(choice, category_choice)

    def category_options(choice, category_choice):
        if choice == 'E':
            option = input("\nWould you like to edit its percentage or categories? (P/C)\n").upper()
        elif choice == "A":
            option = "C"
        sub_category_choice(choice, category_choice, option)

    def sub_category_choice(choice, category_choice, option):
        split_category = 'SA' if category_choice == 'S' else 'FA'
        if choice == 'E':
            if option == "C":
                sub_category = input("\nWhich sub-category would you like to edit?\n").title()
                sub_category_option = input("\nWould you like to edit its percentage or assessments? (P/A)\n").upper()
                if sub_category_option == 'P':
                    percentage_prompt(category_choice, sub_category)
                elif sub_category_option == 'A':
                    bottom_assessment_choice(category_choice, sub_category)
                    pass
            elif option == "P":
                percentage_prompt(category_choice)

        elif choice == "A":
            sub_category_option = input("\nWould you like to add a sub-category or an assessment? (S/A)\n").upper()

            if sub_category_option == "S":
                print(bcolors.OKGREEN + f"\nAdding a sub-category under {split_category}" + bcolors.ENDC)
                sub_category_label = input("Name of sub-category: ").title()
                sub_category_percentage = float(input("Percentage of sub-category (0.01 - 1.00): "))
                create_category(user_id, subject_name, quarter, split_category, sub_category_label, sub_category_percentage)

            elif sub_category_option == "A":
                sub_category = input("\nWhich sub-category would you like to add an assessment to?\n").title()
                assessment_label = input("Name of assessment: ").title()
                score_obtained = float(input("Score obtained: "))
                maximum_score = float(input("Maximum score possible: "))
                create_assessment(user_id, subject_name, quarter, split_category, sub_category, assessment_label, score_obtained, maximum_score)

    def bottom_assessment_choice(category_choice, sub_categ):
        split_category = 'SA' if category_choice == 'S' else 'FA'
        assessment = input("\nWhich assessment would you like to edit?\n").title()

        for sub_category in assessments[split_category]["categories"]:
            if sub_category["label"] == sub_categ:
                sub_category_data = sub_category
                break
        else:
            print(bcolors.BADRED + "Subject not found!" + bcolors.ENDC)
            assessments_view(user_id, quarter, subject_name)
        
        assessment_option = input("\nWould you like to edit its score, or maximum? (S/M)\n").upper()
        assessment_options = {"S": 'score_obtained', "M": 'maximum_score'}

        if assessment_option == "S":
            new_value = float(input("New score obtained: "))
        elif assessment_option == "M":
            new_value = float(input("New maximum score: "))
        
        for _assessment in sub_category_data["assessments"]:
            if _assessment["label"] == assessment:
                _assessment[assessment_options[assessment_option]] = new_value
        
        save_quarter_data(user_id, quarter, quarter_data)
        display_assessments(assessments)
    
    assessment_choice()

def terminal_sequence(user_id, window):
    while True:
        print("\n(Check the window opened for reference!)")
        choice = input("Do you want to add a new subject or edit a quarter's assessments? (S/Q/X)\n").upper()

        if choice == "S":
            add_new_subject(user_id)
            window.after(0, lambda: refresh_table(user_id))

        elif choice == "Q":
            view_quarter(user_id)

        elif choice == "X":
            window.after(0, window.destroy)
            break

## GUI (WINDOW)
def refresh_quarter_table(user_id, quarter):
    global quarter_table
    for row in quarter_table.get_children():
        quarter_table.delete(row)
    
    user_data = get_user_data(user_id)
    quarter_data = get_quarter_data(user_id, quarter)
    for subject, quarter in zip(user_data["subjects"], quarter_data):
        name = subject["name"]
        grade = quarter[name]["grade"]
        passed = quarter[name]["passed"]
        quarter_table.insert("", tk.END, values=(name, grade, passed))

def quarter_table_window():
    global window, quarter_window, quarter_table
    quarter_window = tk.Toplevel(window)
    quarter_table = build_table(quarter_window, ("Subject", "Grade", "Remarks"))

def refresh_table(user_id):
    global table
    for row in table.get_children():
        table.delete(row)
    
    user_data = get_user_data(user_id)
    for subject in user_data["subjects"]:
        name = subject["name"]
        unit = subject["unit"]
        grades = [quarter["grade"] for quarter in subject["quarters"]]
        final = subject["final"]
        classification = subject["classification"]
        row_data = grades.copy()
        row_data.insert(0, name)
        row_data.append(final)
        row_data.append(unit)
        row_data.append(classification)
        table.insert("", tk.END, values=row_data)


def build_table(window, columns):
    table_frame = tk.Frame(window)
    table_frame.pack(expand=True)

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
    global window
    # Prompted GPT on how to multi-thread tk window and terminal interaction
    window = tk.Tk()
    window.title("Report Card Table")

    global table
    table = build_table(window, ("Subject", "Q1", "Q2", "Q3", "Q4", "Final", "Unit", "Classification"))
    refresh_table(user_id)

    terminal_thread = threading.Thread(
        target=terminal_sequence,
        args=(user_id, window),
        daemon=True
    )
    terminal_thread.start()

    window.mainloop()
def main():
    if user_id := auth_sequence():
        sequence(user_id)

main()
