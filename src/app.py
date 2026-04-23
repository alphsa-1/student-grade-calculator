from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

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
        name TEXT NOT NULL UNIQUE
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
        assessment_type_id INTEGER NOT NULL,
        label TEXT NOT NULL,
        percentage REAL,
        FOREIGN KEY (assessment_type_id) REFERENCES categories(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        label TEXT NOT NULL,
        score_obtained REAL NOT NULL,
        maximum_score REAL NOT NULL,
        FOREIGN KEY (category_id) REFERENCES sub_categories(id) ON DELETE CASCADE
    );
    """)

    conn.commit()

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

class UserService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create(self, name):
        self.db.execute(
            "INSERT INTO users (name) VALUES (?)",
            (name,),
            commit=True
        )

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
    
    def get_user_id_by_name(self, name):
        row = self.db.execute(
            "SELECT id FROM users WHERE name=?",
            (name,)
        ).fetchone()

        return row["id"] if row else None

class SubjectService:
    def __init__(self, db: DatabaseManager, grade_service):
        self.db = db
        self.grade_service = grade_service

    def create(self, user_id, name, unit):
        cursor = self.db.execute(
            "INSERT INTO subjects (user_id, name, unit) VALUES (?, ?, ?)",
            (user_id, name, unit),
            commit=True
        )
        return cursor.lastrowid

    def get_subject(self, user_id, name):
        subject = self.db.execute(
            "SELECT * FROM subjects WHERE user_id = (?) AND name = (?)",
            (user_id, name),
            commit=True
        )

        return subject

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

    def delete(self, subject_id):
        self.db.execute(
            "DELETE FROM subjects WHERE id=?",
            (subject_id,),
            commit=True
        )
	
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

class GradeService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    # QUARTER
    def create_quarter(self, subject_id, quarter):
        cursor = self.db.execute(
            "INSERT INTO quarters (subject_id, quarter) VALUES (?, ?)",
            (subject_id, quarter),
            commit=True
        )
        return cursor.lastrowid

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
                "assessments": self.get_assessment_types(quarter_id),
                "grade": grade,
                "passed": passed
            })

        return result

    def get_quarter(self, quarter_number, subject_id):
        quarter = self.db.execute(
            "SELECT * FROM quarters WHERE quarter = ? AND subject_id = ?",
            (quarter_number, subject_id,)
        ).fetchone()

        return quarter

    # SA / FA
    def create_assessment_type(self, quarter_id, type_, percentage):
        cursor = self.db.execute(
            """INSERT INTO categories (quarter_id, type, percentage)
               VALUES (?, ?, ?)""",
            (quarter_id, type_, percentage),
            commit=True
        )
        return cursor.lastrowid

    def get_assessment_types(self, quarter_id):
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
                "sub_categories": self.get_categories(at_id)
            }

        return result

    def get_assessment_type(self, quarter_id, type):
        assessment_type = self.db.execute(
            "SELECT * FROM categories WHERE quarter_id = ? AND type = ?",
            (quarter_id, type,)
        ).fetchone()

        print(assessment_type)
        return assessment_type

    # CATEGORY
    def create_category(self, assessment_type_id, label, percentage):
        cursor = self.db.execute(
            """INSERT INTO sub_categories (assessment_type_id, label, percentage)
               VALUES (?, ?, ?)""",
            (assessment_type_id, label, percentage),
            commit=True
        )
        return cursor.lastrowid

    def get_categories(self, assessment_type_id):
        rows = self.db.execute(
            "SELECT id, label, percentage FROM sub_categories WHERE assessment_type_id=?",
            (assessment_type_id,)
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

    def get_category(self, assessment_type_id, label):
        category = self.db.execute(
            "SELECT * FROM sub_categories WHERE assessment_type_id = ? AND label = ?",
            (assessment_type_id, label,)
        ).fetchone()

        return category

    # ITEM
    def create_item(self, category_id, label, score, max_score):
        self.db.execute(
            """INSERT INTO items 
               (category_id, label, score_obtained, maximum_score)
               VALUES (?, ?, ?, ?)""",
            (category_id, label, score, max_score),
            commit=True
        )

    def update_item(self, item_id, score, max_score):
        self.db.execute(
            """UPDATE items 
               SET score_obtained=?, maximum_score=? 
               WHERE id=?""",
            (score, max_score, item_id),
            commit=True
        )

    def delete_item(self, item_id):
        self.db.execute(
            "DELETE FROM items WHERE id=?",
            (item_id,),
            commit=True
        )

    def get_items(self, category_id):
        rows = self.db.execute(
            """SELECT label, score_obtained, maximum_score 
            FROM items WHERE category_id=?""",
            (category_id,)
        ).fetchall()

        return [
            {
                "label": r[0],
                "score_obtained": r[1],
                "maximum_score": r[2]
            }
            for r in rows
        ]

    def get_item(self, category_id, label):
        item = self.db.execute(
            "SELECT * FROM items WHERE category_id = ? AND label = ?",
            (category_id, label,)
        )

        return item

# Startup
db = DatabaseManager()
user_service = UserService(db)
grade_service = GradeService(db)
subject_service = SubjectService(db, grade_service)

# Inject test data
@app.route("/seed")
def seed_data():
    subj_id = subject_service.create(1, "Physics", 1.7)

    for i in range(1, 5):
        grade_service.create_quarter(subj_id, i)

    quarter = grade_service.get_quarter(1, subj_id)
    quarter_id = quarter["id"]

    grade_service.create_assessment_type(quarter_id, "SA", 0.7)
    grade_service.create_assessment_type(quarter_id, "FA", 0.3)

    at = grade_service.get_assessment_type(quarter_id, "SA")
    at_id = at["id"]

    grade_service.create_category(at_id, "Long Test", 0.5)

    cat = grade_service.get_category(at_id, "Long Test")
    cat_id = cat["id"]

    grade_service.create_item(cat_id, "Long Test 1", 37, 40)

    return jsonify({"message": "seeded successfully"})

# Debug
@app.route("/fresh")
def refresh():
    conn = get_db_connection("src/grades.db")
    cursor = conn.cursor()
    cursor.executescript("""
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
