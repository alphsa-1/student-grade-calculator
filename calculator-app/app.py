from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

# Connect to SQLite (creates file if it doesn't exist)
def get_db_connection():
    conn = sqlite3.connect('calculator.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create table if it doesn't exist
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num1 REAL,
            num2 REAL,
            operation TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    num1 = float(data['num1'])
    num2 = float(data['num2'])
    operation = data['operation']

    result = 0

    if operation == "add":
        result = num1 + num2
    elif operation == "subtract":
        result = num1 - num2
    elif operation == "multiply":
        result = num1 * num2
    elif operation == "divide":
        result = num1 / num2 if num2 != 0 else "Error"

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO calculations (num1, num2, operation, result) VALUES (?, ?, ?, ?)",
        (num1, num2, operation, str(result))
    )
    conn.commit()
    conn.close()

    return jsonify({"result": result})

@app.route('/history', methods=['GET'])
def history():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM calculations ORDER BY id DESC LIMIT 10"
    ).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])

if __name__ == '__main__':
    init_db()  # create table automatically
    app.run(debug=True)