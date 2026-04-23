from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('src/grades.db')
    conn.row_factory = sqlite3.Row
    return conn

# Used to create the tables if they don't exist
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY
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

    CREATE TABLE IF NOT EXISTS assessment_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quarter_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        percentage REAL,
        FOREIGN KEY (quarter_id) REFERENCES quarters(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_type_id INTEGER NOT NULL,
        label TEXT NOT NULL,
        percentage REAL,
        FOREIGN KEY (assessment_type_id) REFERENCES assessment_types(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS assessment_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        label TEXT NOT NULL,
        score_obtained REAL NOT NULL,
        maximum_score REAL NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
    );
    """)

    conn.commit()

# Starts the program
if __name__ == '__main__':
    init_db() # Creates the tables initially
    app.run(debug=True) # Actually start running it