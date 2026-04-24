from flask import Flask, request, jsonify, render_template
import sqlite3

# Flask framework start
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# Connects to database
def get_db_connection(db_name):
    conn = sqlite3.connect(
        db_name,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn

# Used to create the tables if they don't exist
def init_db():
    conn = get_db_connection("src/grades.db")
    cursor = conn.cursor()
    cursor.executescript("""         
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        unit REAL NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS quarters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        quarter INTEGER NOT NULL,
        grade REAL,
        passed TEXT,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quarter_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        percentage REAL,
        FOREIGN KEY (quarter_id) REFERENCES quarters(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS sub_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        label TEXT NOT NULL,
        percentage REAL,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sub_category_id INTEGER NOT NULL,
        label TEXT NOT NULL,
        score_obtained REAL NOT NULL,
        maximum_score REAL NOT NULL,
        FOREIGN KEY (sub_category_id) REFERENCES sub_categories(id) ON DELETE CASCADE
    );
    """)

    conn.commit()

## Database Manipulation (CRUD)
# Manager for the services, connects to the database and executes lines
class DatabaseManager:
    def __init__(self, db_name="src/grades.db"):
        self.conn = get_db_connection(db_name)
        self.cursor = self.conn.cursor()

    def execute(self, query, params=(), commit=False):
        self.cursor.execute(query, params)
        if commit:
            self.conn.commit()
        return self.cursor

    def close(self):
        self.conn.close()

# Handles user-related database manipulation
class UserService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    # Creates user entry
    def create(self, name, password):
        cursor = self.db.execute(
            "INSERT INTO users (name, password) VALUES (?, ?)",
            (name, password),
            commit=True
        )

        return cursor.lastrowid

    # Gets user 
    def get(self, user_id):
        return self.db.execute(
            "SELECT * FROM users WHERE id=?",
            (user_id,)
        ).fetchone()

    def delete(self, user_id):
        self.db.execute(
            "DELETE FROM users WHERE id=?",
            (user_id,),
            commit=True
        )
    
    # Gets user id by name
    def get_user_id_by_name(self, name):
        row = self.db.execute(
            "SELECT id FROM users WHERE name=?",
            (name,)
        ).fetchone()

        return row["id"] if row else None

# Handles per-subject
class SubjectService:
    def __init__(self, db: DatabaseManager, grade_service):
        self.db = db
        self.grade_service = grade_service

    # Creates a subject entry
    def create(self, user_id, name, unit):
        cursor = self.db.execute(
            "INSERT INTO subjects (user_id, name, unit) VALUES (?, ?, ?)",
            (user_id, name, unit),
            commit=True
        )
        return cursor.lastrowid

    # Returns a subject from query
    def get_subject(self, user_id, name):
        subject = self.db.execute(
            "SELECT * FROM subjects WHERE user_id = (?) AND name = (?)",
            (user_id, name),
            commit=True
        )

        return subject

    # Updates subject name or unit
    def update(self, subject_id, name=None, unit=None):
        if name:
            self.db.execute(
                "UPDATE subjects SET name=? WHERE id=?",
                (name, subject_id),
                commit=True
            )
        if unit:
            self.db.execute(
                "UPDATE subjects SET unit=? WHERE id=?",
                (unit, subject_id),
                commit=True
            )

    # Deletes a subject if needed
    def delete(self, subject_id):
        self.db.execute(
            "DELETE FROM subjects WHERE id=?",
            (subject_id,),
            commit=True
        )
	
    # Gets the entire data of the user
    def get_full_subjects(self, user_id):
        subjects = self.db.execute(
            "SELECT id, name, unit FROM subjects WHERE user_id=?",
            (user_id,)
        ).fetchall()

        result = []
        for subject in subjects:
            subject_id, name, unit = subject

            result.append({
                "name": name,
                "unit": unit,
                "quarters": self.grade_service.get_quarters(subject_id),
                "final": None,
                "classification": None
            })

        return result

# Handles quarters - items
class GradeService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    ## QUARTER

    # Creates a quarter entry (need to call individually four times)
    def create_quarter(self, subject_id, quarter):
        cursor = self.db.execute(
            "INSERT INTO quarters (subject_id, quarter) VALUES (?, ?)",
            (subject_id, quarter),
            commit=True
        )
        return cursor.lastrowid

    # Returns 4 quarters of a subject from a query
    def get_quarters(self, subject_id):
        quarters = self.db.execute(
            "SELECT id, quarter, grade, passed FROM quarters WHERE subject_id=?",
            (subject_id,)
        ).fetchall()

        result = []

        for quarter in quarters:
            quarter_id, quarter, grade, passed = quarter

            result.append({
                "quarter": quarter,
                "assessments": self.get_categories(quarter_id),
                "grade": grade,
                "passed": passed
            })

        return result

    # Returns a specific quarter using its number and subject id
    def get_quarter(self, quarter_number, subject_id):
        quarter = self.db.execute(
            "SELECT * FROM quarters WHERE quarter = ? AND subject_id = ?",
            (quarter_number, subject_id,)
        ).fetchone()

        return quarter

    ## SA / FA (Category)

    # Creates category entry (call two times individually)
    def create_category(self, quarter_id, type_, percentage):
        cursor = self.db.execute(
            """INSERT INTO categories (quarter_id, type, percentage)
               VALUES (?, ?, ?)""",
            (quarter_id, type_, percentage),
            commit=True
        )
        return cursor.lastrowid

    # Gets the two categories of a quarter
    def get_categories(self, quarter_id):
        rows = self.db.execute(
            "SELECT id, type, percentage FROM categories WHERE quarter_id=?",
            (quarter_id,)
        ).fetchall()

        result = {"SA": {"percentage": None, "sub_categories": []},
                "FA": {"percentage": None, "sub_categories": []}}

        for r in rows:
            at_id, type_, percentage = r

            result[type_] = {
                "percentage": percentage,
                "sub_categories": self.get_sub_categories(at_id)
            }

        return result

    # Get specifc category using type and quarter id
    def get_category(self, quarter_id, type):
        category = self.db.execute(
            "SELECT * FROM categories WHERE quarter_id = ? AND type = ?",
            (quarter_id, type,)
        ).fetchone()

        return category

    ## SUB-CATEGORY

    # Creates a sub-category entry
    def create_sub_category(self, category_id, label, percentage):
        cursor = self.db.execute(
            """INSERT INTO sub_categories (category_id, label, percentage)
               VALUES (?, ?, ?)""",
            (category_id, label, percentage),
            commit=True
        )
        return cursor.lastrowid

    # Returns all sub-categories of a category
    def get_sub_categories(self, category_id):
        rows = self.db.execute(
            "SELECT id, label, percentage FROM sub_categories WHERE category_id=?",
            (category_id,)
        ).fetchall()

        result = []

        for r in rows:
            cat_id, label, percentage = r

            result.append({
                "label": label,
                "percentage": percentage,
                "assessments": self.get_items(cat_id)
            })

        return result

    # Returns a category based off its label and category id
    def get_sub_category(self, category_id, label):
        category = self.db.execute(
            "SELECT * FROM sub_categories WHERE category_id = ? AND label = ?",
            (category_id, label,)
        ).fetchone()

        return category

    ## ITEM

    # Creates an item entry
    def create_item(self, sub_category_id, label, score, max_score):
        self.db.execute(
            """INSERT INTO items 
               (sub_category_id, label, score_obtained, maximum_score)
               VALUES (?, ?, ?, ?)""",
            (sub_category_id, label, score, max_score),
            commit=True
        )

    # Updates the items value
    def update_item(self, item_id, score, max_score):
        self.db.execute(
            """UPDATE items 
               SET score_obtained=?, maximum_score=? 
               WHERE id=?""",
            (score, max_score, item_id),
            commit=True
        )

    # Deletes an item entry
    def delete_item(self, item_id):
        self.db.execute(
            "DELETE FROM items WHERE id=?",
            (item_id,),
            commit=True
        )

    # Gets all items under a sub_category
    def get_items(self, sub_category_id):
        rows = self.db.execute(
            """SELECT label, score_obtained, maximum_score 
            FROM items WHERE sub_category_id = ?""",
            (sub_category_id,)
        ).fetchall()

        return [
            {
                "label": r[0],
                "score_obtained": r[1],
                "maximum_score": r[2]
            }
            for r in rows
        ]

    # Gets a specific item based off its label and sub-category id
    def get_item(self, sub_category_id, label):
        item = self.db.execute(
            "SELECT * FROM items WHERE sub_category_id = ? AND label = ?",
            (sub_category_id, label,)
        )

        return item

# Startup
db = DatabaseManager()
user_service = UserService(db)
grade_service = GradeService(db)
subject_service = SubjectService(db, grade_service)

@app.route("/signup", methods=['POST'])
def signup():
    credentials = request.json
    global _user_id
    
    # Creates new user
    try:
        _user_id = user_service.create(credentials["username"], credentials["password"])
        return jsonify({"message": "success"}), 200
    except:
        return jsonify({"error": "failed"}), 400
        
@app.route("/login", methods=['POST'])
def login():
    credentials = request.json
    global _user_id

    # Searches for matching credentials
    conn = get_db_connection("src/grades.db")
    cursor = conn.cursor()
    user = cursor.execute(
        "SELECT * FROM users WHERE name = ? AND password = ?",
        (credentials["username"], credentials["password"])
    ).fetchone()

    # Logins successfully
    if user is not None:
        _user_id = user["id"]
        return jsonify({"userId": _user_id}), 200 # Returns user id to frontend
    else:
        return jsonify({"error": "failed"}), 401 # Unsuccessful Login Attempt

def create_empty_subject_data(user_id, name, unit):
    subject_id = subject_service.create(user_id, name, unit)
    for i in range(1, 5):
        quarter_id = grade_service.create_quarter(subject_id, i)
        grade_service.create_category(quarter_id, "SA", 0)
        grade_service.create_category(quarter_id, "FA", 0)

def compute_sub_category_grade(sub_category):
    obtained_sum = 0
    maximum_sum = 0

    for item in sub_category["assessments"]:
        obtained_sum += item["score_obtained"]
        maximum_sum += item["maximum_score"]

    if maximum_sum == 0:
        return 0

    raw = obtained_sum / maximum_sum
    return raw * sub_category["percentage"]

def compute_category_grade(category_data):
    total = 0

    for sub in category_data["sub_categories"]:
        total += compute_sub_category_grade(sub)

    return total * (category_data["percentage"] or 0)

def compute_quarter_grade(subject_id, quarter_number):
    quarter = grade_service.get_quarter(quarter_number, subject_id)
    quarter_id = quarter["id"]

    categories = grade_service.get_categories(quarter_id)

    sa = compute_category_grade(categories["SA"])
    fa = compute_category_grade(categories["FA"])

    return sa + fa

def compute_quarter_gwa(user_id, quarter_number):

    conn = get_db_connection("src/grades.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.unit, q.grade
        FROM subjects s
        JOIN quarters q ON q.subject_id = s.id
        WHERE s.user_id = ? AND q.quarter = ?
    """, (user_id, quarter_number))

    rows = cursor.fetchall()

    total_weighted = 0
    total_units = 0

    for row in rows:
        unit = row["unit"]
        grade = row["grade"]

        if grade is not None:
            total_weighted += grade * unit
            total_units += unit

    if total_units == 0:
        return None

    return total_weighted / total_units

def compute_subject_final(subject_id):
    conn = get_db_connection("src/grades.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT grade
        FROM quarters
        WHERE subject_id = ?
        ORDER BY quarter ASC
    """, (subject_id,))

    rows = cursor.fetchall()

    values = [row["grade"] for row in rows if row["grade"] is not None]

    if not values:
        return None

    result = convert(values[0])

    for quarter in values[1:]:
        result = cascade_quarter_grade(result, convert(quarter))

    return result

def compute_final_gwa(user_id):
    conn = get_db_connection("src/grades.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, unit
        FROM subjects
        WHERE user_id = ?
    """, (user_id,))

    subjects = cursor.fetchall()

    total_weighted = 0
    total_units = 0

    for subject in subjects:
        subject_id = subject["id"]
        unit = subject["unit"]

        final = compute_subject_final(subject_id)
        print(final, unit)

        if final is not None:
            total_weighted += final * unit
            total_units += unit

    if total_units == 0:
        return None

    return round(total_weighted / total_units, 2)

def classify_gwa(gwa):
    if gwa is None:
        return None
    if gwa <= 1.50:
        return "Director's Lister"
    elif gwa <= 2.25:
        return "Standard"
    elif gwa <= 3.00:
        return "Sub-Standard"
    elif gwa <= 4.00:
        return "Probation"
    elif gwa == 5.00:
        return "Termination"

def cascade_quarter_grade(current, quarter_grade):
    current = (current * (1/3)) + (quarter_grade * (2/3))
    # truncate to 3 decimal places
    current = int(current * 1000) / 1000

    if 1.000 <= current <= 1.125:
        return 1.00
    elif 1.126 <= current <= 1.375:
        return 1.25
    elif 1.376 <= current <= 1.625:
        return 1.50
    elif 1.626 <= current <= 1.875:
        return 1.75
    elif 1.876 <= current <= 2.125:
        return 2.00
    elif 2.126 <= current <= 2.375:
        return 2.25
    elif 2.376 <= current <= 2.625:
        return 2.50
    elif 2.626 <= current <= 2.875:
        return 2.75
    elif 2.876 <= current <= 3.500:
        return 3.00
    elif 3.501 <= current <= 4.500:
        return 4.00
    elif 4.501 <= current <= 5.000:
        return 5.00
    else:
        return None  # invalid grade

def convert(raw):
    converted = 0
    if raw is None:
        return None
    elif raw >= 96:
        converted = 1.00
    elif raw >= 90:
        converted = 1.25
    elif raw >= 84:
        converted = 1.50
    elif raw >= 78:
        converted = 1.75
    elif raw >= 72:
        converted = 2.00
    elif raw >= 66:
        converted = 2.25
    elif raw >= 60:
        converted = 2.50
    elif raw >= 55:
        converted = 2.75
    elif raw >= 50:
        converted = 3.00
    elif raw >= 40:
        converted = 4.00
    else:
        converted = 5.00
    
    return converted

# Subjects routes
@app.route("/subjects/<int:user_id>/<int:subject_id>", methods=["PUT"])
def update_subject(user_id, subject_id):
    data = request.json
    subject_service.update(subject_id, data["name"], data["unit"])

    return jsonify({"message": "success"}), 200

@app.route("/subjects/<int:user_id>", methods=["POST"])
def create_subject(user_id):
    data = request.json
    try:
        subj_id = subject_service.create(user_id, data["name"], data["unit"])
        for i in range(1, 5):
            grade_service.create_quarter(subj_id, i)

        return jsonify({"message": "success"}), 201
    except:
        return jsonify({"error": "Create failed"}), 422   

@app.route("/subjects/<int:user_id>", methods=["GET"])
def load_card_table(user_id):
    conn = get_db_connection("src/grades.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        s.id,
        s.name, 
        s.unit,

        MAX(CASE WHEN q.quarter = 1 THEN q.grade END) AS quarter1Grade,
        MAX(CASE WHEN q.quarter = 2 THEN q.grade END) AS quarter2Grade,
        MAX(CASE WHEN q.quarter = 3 THEN q.grade END) AS quarter3Grade,
        MAX(CASE WHEN q.quarter = 4 THEN q.grade END) AS quarter4Grade

    FROM subjects s
    LEFT JOIN quarters q ON q.subject_id = s.id

    WHERE s.user_id = ?

    GROUP BY s.id, s.name, s.unit
    ORDER BY s.id ASC;
    """, (user_id,))

    rows = cursor.fetchall()

    subjects = []

    for row in rows:
        subject = dict(row)

        subject_id = subject["id"]

        # compute subject final
        final = compute_subject_final(subject_id)
        subject["final"] = final
        subject["classification"] = classify_gwa(subject["final"])

        # convert quarter grades
        for quarter in ["quarter1Grade", "quarter2Grade", "quarter3Grade", "quarter4Grade"]:
            subject[quarter] = convert(subject[quarter])

        subjects.append(subject)

    q1 = compute_quarter_gwa(user_id, 1)
    q2 = compute_quarter_gwa(user_id, 2)
    q3 = compute_quarter_gwa(user_id, 3)
    q4 = compute_quarter_gwa(user_id, 4)

    final_gwa = compute_final_gwa(user_id)

    # total units
    cursor.execute("""
        SELECT SUM(unit) as total_units
        FROM subjects
        WHERE user_id = ?
    """, (user_id,))
    total_units = cursor.fetchone()["total_units"] or 0

    gwa_data = {
        "q1": convert(q1),
        "q2": convert(q2),
        "q3": convert(q3),
        "q4": convert(q4),
        "final": final_gwa,
        "units": total_units,
        "classification": classify_gwa(final_gwa)
    }

    return jsonify({
        "subjects": subjects,
        "gwa": gwa_data
    }), 200

# Quarters routes
@app.route("/quarters/<int:user_id>/<int:quarter>", methods=["GET"])
def load_quarter_table(user_id, quarter):
    conn = get_db_connection("src/grades.db")
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        q.id,
        s.name, 
        q.grade,
        q.passed

    FROM subjects s
    LEFT JOIN quarters q ON q.subject_id = s.id AND q.quarter = ?

    WHERE s.user_id = ?
    GROUP BY s.id, s.name, s.unit
    ORDER BY s.id ASC;
    """, (quarter, user_id))

    rows = cursor.fetchall()

    subjects = [dict(row) for row in rows]

    for subject in subjects:
            converted_grade = convert(subject["grade"])
            subject["grade"] = converted_grade
            subject["passed"] = classify_gwa(subject["grade"])

    return jsonify(subjects), 200

# Assessments routes
@app.route("/assessments/<int:quarter_id>", methods=["GET"])
def load_assessment_table(quarter_id):
    conn = get_db_connection("src/grades.db")
    cursor = conn.cursor()

    # get categories first
    cursor.execute("""
        SELECT id, type, percentage
        FROM categories
        WHERE quarter_id = ?
        ORDER BY id
    """, (quarter_id,))
    categories_rows = cursor.fetchall()

    categories = {
        row["id"]: {
            "id": row["id"],
            "type": row["type"],
            "percentage": row["percentage"],
            "sub_categories": {}
        }
        for row in categories_rows
    }

    category_ids = tuple(categories.keys()) or (0,)

    # then sub categories
    cursor.execute(f"""
        SELECT id, label, percentage, category_id
        FROM sub_categories
        WHERE category_id IN ({",".join(["?"] * len(category_ids))})
    """, category_ids)

    sub_rows = cursor.fetchall()

    sub_map = {}

    for row in sub_rows:
        sub_map[row["id"]] = {
            "id": row["id"],
            "label": row["label"],
            "percentage": row["percentage"],
            "category_id": row["category_id"],
            "items": []
        }
        # remap each sub category to each category
        categories[row["category_id"]]["sub_categories"][row["id"]] = sub_map[row["id"]]

    sub_ids = tuple(sub_map.keys()) or (0,)

    # finally get items
    cursor.execute(f"""
        SELECT id, label, score_obtained, maximum_score, sub_category_id
        FROM items
        WHERE sub_category_id IN ({",".join(["?"] * len(sub_ids))})
    """, sub_ids)

    item_rows = cursor.fetchall()

    # append each item to its corresponding sub category
    for row in item_rows:
        sub_map[row["sub_category_id"]]["items"].append({
            "id": row["id"],
            "label": row["label"],
            "score_obtained": row["score_obtained"],
            "maximum_score": row["maximum_score"]
        })

    # now collate
    result = []

    for cat in categories.values():
        cat["sub_categories"] = list(cat["sub_categories"].values())
        result.append(cat)

    return {
        "categories": result
    }, 200

@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json()

    quarter_id = data["quarterId"]
    categories = data["categories"]

    conn = sqlite3.connect("src/grades.db")
    cursor = conn.cursor()

    # delete existing first
    cursor.execute("""
        DELETE FROM categories
        WHERE quarter_id = ?
    """, (quarter_id,))

    # insert new and calculate
    quarter_total = 0

    for cat in categories:
        # insert category
        cursor.execute("""
            INSERT INTO categories (type, percentage, quarter_id)
            VALUES (?, ?, ?)
        """, (cat["type"], cat["percentage"], quarter_id))

        category_id = cursor.lastrowid

        category_total = 0

        for sub in cat["sub_categories"]:
            cursor.execute("""
                INSERT INTO sub_categories (label, percentage, category_id)
                VALUES (?, ?, ?)
            """, (sub["label"], sub["percentage"], category_id))

            sub_id = cursor.lastrowid

            sub_total = 0
            total_score_obtained = 0
            total_maximum_score = 0

            for item in sub["items"]:
                score_obtained = item["score_obtained"]
                maximum_score = item["maximum_score"]

                percent_score = (score_obtained / maximum_score) * 100 if maximum_score else 0
                total_score_obtained += score_obtained
                total_maximum_score += maximum_score

                cursor.execute("""
                    INSERT INTO items (label, score_obtained, maximum_score, sub_category_id)
                    VALUES (?, ?, ?, ?)
                """, (item["label"], score_obtained, maximum_score, sub_id))

            # subcategory average
            sub_total = (total_score_obtained / total_maximum_score) * 100

            category_total += sub_total * (sub["percentage"] / 100)

        # category weighted contribution
        category_weighted = category_total * (cat["percentage"] / 100)

        quarter_total += category_weighted

    # compute final grade and remarks
    final_grade = round(quarter_total, 2)

    converted_grade = convert(final_grade)

    if converted_grade >= 60:
        passed = "Passed"
    else:
        passed = "Failed"

    cursor.execute("""
        UPDATE quarters
        SET grade = ?, passed = ?
        WHERE id = ?
    """, (final_grade, passed, quarter_id))

    conn.commit()

    return jsonify({
        "quarter_id": quarter_id,
        "raw_grade": final_grade,
        "converted_grade": converted_grade,
        "passed": passed
}), 200

# Inject test data
@app.route("/seed")
def seed_data():
    subj_id = subject_service.create(1, "Physics", 1.7)

    for i in range(1, 5):
        grade_service.create_quarter(subj_id, i)

    quarter = grade_service.get_quarter(1, subj_id)
    quarter_id = quarter["id"]

    grade_service.create_category(quarter_id, "SA", 0.7)
    grade_service.create_category(quarter_id, "FA", 0.3)

    at = grade_service.get_category(quarter_id, "SA")
    at_id = at["id"]

    grade_service.create_sub_category(at_id, "Long Test", 1)

    cat = grade_service.get_sub_category(at_id, "Long Test")
    cat_id = cat["id"]

    grade_service.create_item(cat_id, "Long Test 1", 37, 40)

    return jsonify({"message": "seeded successfully", "grade": compute_quarter_grade(1, 1)})

# Debug
@app.route("/fresh")
def refresh():
    conn = get_db_connection("src/grades.db")
    cursor = conn.cursor()
    cursor.executescript("""
    DROP TABLE users;
    DROP TABLE subjects;
    DROP TABLE quarters;
    DROP TABLE sub_categories;
    DROP TABLE categories;
    DROP TABLE items;
    """)
    init_db()
    return jsonify({"message": "db refreshed successfully"})

# Starts the program
if __name__ == '__main__':
    init_db() # Creates the tables initially
    app.run(debug=True) # Actually start running it
