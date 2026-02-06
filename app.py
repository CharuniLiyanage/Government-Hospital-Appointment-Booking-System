from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

APPOINTMENT_DURATION = 15  # minutes


# ----------------------
# DATABASE SETUP
# ----------------------
def init_db():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS department (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            department_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reference_no TEXT NOT NULL,
            UNIQUE(department_id, appointment_date, appointment_time)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM department")
    if cursor.fetchone()[0] == 0:
        departments = [
            "General Physician", "Cardiology", "Pediatrics", "Neurology",
            "Orthopedics", "Dermatology", "ENT", "Ophthalmology",
            "Gynecology", "Psychiatry", "Urology", "Gastroenterology",
            "Nephrology", "Pulmonology", "Rheumatology", "Oncology",
            "Endocrinology", "Hematology", "Pediatrics Surgery", "Cardiac Surgery"
        ]
        for d in departments:
            cursor.execute("INSERT INTO department (name) VALUES (?)", (d,))

    db.commit()
    db.close()


if not os.path.exists(DB_PATH):
    init_db()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------
# ROUTES
# ----------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/book", methods=["POST"])
def book():
    name = request.form["name"].strip()
    department = request.form["department"]
    date = request.form["date"]
    time_str = request.form["time"]

    db = get_db()

    start_req = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
    end_req = start_req + timedelta(minutes=APPOINTMENT_DURATION)

    existing = db.execute("""
        SELECT appointment_time FROM appointment
        WHERE department_id = ? AND appointment_date = ?
    """, (department, date)).fetchall()

    for row in existing:
        start = datetime.strptime(f"{date} {row['appointment_time']}", "%Y-%m-%d %H:%M")
        end = start + timedelta(minutes=APPOINTMENT_DURATION)

        if start_req < end and end_req > start:
            db.close()
            return jsonify({
                "status": "error",
                "message": f"This time slot is not available. Choose another {APPOINTMENT_DURATION}-minute slot."
            }), 400

    ref_no = "HOSP-" + uuid.uuid4().hex[:8].upper()

    db.execute("""
        INSERT INTO appointment (patient_name, department_id, appointment_date, appointment_time, reference_no)
        VALUES (?, ?, ?, ?, ?)
    """, (name, department, date, time_str, ref_no))

    db.commit()
    db.close()

    return jsonify({
        "status": "success",
        "reference_no": ref_no
    })


@app.route("/my_appointments", methods=["GET", "POST"])
def my_appointments():
    appointments = []
    name = ""

    if request.method == "POST":
        name = request.form["name"].strip()
        db = get_db()
        appointments = db.execute("""
            SELECT d.name AS department, a.appointment_date, a.appointment_time, a.reference_no
            FROM appointment a
            JOIN department d ON a.department_id = d.id
            WHERE LOWER(a.patient_name) = LOWER(?)
            ORDER BY a.appointment_date, a.appointment_time
        """, (name,)).fetchall()
        db.close()

    return render_template("my_appointments.html", appointments=appointments, name=name)


@app.route("/view_doctors")
def view_doctors():
    dept_dict = {
        "General Physician": [
            "Dr. Amal Perera",
            "Dr. Nadeesha Silva",
            "Dr. Tharindu Jayasinghe"
        ],
        "Cardiology": [
            "Dr. Sanjeewa Kumara",
            "Dr. Dilani Fernando"
        ],
        "Pediatrics": [
            "Dr. Hasini Perera",
            "Dr. Chamodi Wickramasinghe"
        ],
        "Neurology": [
            "Dr. Kasun Rathnayake",
            "Dr. Samanthi Gunawardena"
        ],
        "Orthopedics": [
            "Dr. Pradeep Wijesinghe",
            "Dr. Mahesh Karunarathne"
        ],
        "Dermatology": [
            "Dr. Anushka Fernando",
            "Dr. Sachini Perera"
        ],
        "ENT": [
            "Dr. Ruwan Jayalath",
            "Dr. Nimesha Silva"
        ],
        "Ophthalmology": [
            "Dr. Nalin Abeysekara",
            "Dr. Shashika Perera"
        ],
        "Gynecology": [
            "Dr. Priyanka Senanayake",
            "Dr. Thilini Rathnayake"
        ],
        "Psychiatry": [
            "Dr. Ishan de Silva",
            "Dr. Madushi Fernando"
        ],
        "Urology": [
            "Dr. Chamath Rodrigo",
            "Dr. Indika Jayawardena"
        ],
        "Gastroenterology": [
            "Dr. Nishan Perera",
            "Dr. Udara Silva"
        ],
        "Nephrology": [
            "Dr. Ranjith Kumara",
            "Dr. Lakmini Jayasekara"
        ],
        "Pulmonology": [
            "Dr. Supun Fernando",
            "Dr. Oshani Perera"
        ],
        "Rheumatology": [
            "Dr. Kanishka Wijeratne"
        ],
        "Oncology": [
            "Dr. Prasad Abeywickrama",
            "Dr. Dilani Karunaratne"
        ],
        "Endocrinology": [
            "Dr. Senuri Jayawardena"
        ],
        "Hematology": [
            "Dr. Buddhika Perera"
        ],
        "Pediatrics Surgery": [
            "Dr. Kavinda Silva"
        ],
        "Cardiac Surgery": [
            "Dr. Asela Wickramasinghe"
        ]
    }
    return render_template("view_doctors.html", dept_dict=dept_dict)


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True)
