from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import os
import uuid
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "rathnapura_hospital_secure_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# ----------------------
# DATABASE SETUP
# ----------------------
def init_db():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    # 1. Departments Table
    cursor.execute("CREATE TABLE IF NOT EXISTS department (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")

    # 2. Doctors Table (Created before populating data)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            dept_id INTEGER,
            FOREIGN KEY (dept_id) REFERENCES department (id)
        )
    """)

    # 3. Appointments Table (FIXED: Correct spacing and structure)
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

    # 4. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            address TEXT,
            age INTEGER,
            phone TEXT,
            email TEXT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # --- POPULATE DATA ---

    # A. Populate Departments FIRST
    cursor.execute("SELECT COUNT(*) FROM department")
    if cursor.fetchone()[0] == 0:
        depts = ["General Physician", "Cardiology", "Pediatrics", "Neurology", 
                 "Orthopedics", "Dermatology", "ENT", "Ophthalmology", 
                 "Gynecology", "Psychiatry"]
        for d in depts:
            cursor.execute("INSERT INTO department (name) VALUES (?)", (d,))
        print("✅ Departments seeded.")

    # B. Populate Doctors SECOND (IDs now match Departments)
    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        doctors_list = [
            ("Dr. Priyantha Bandara", "Senior Consultant", 1),
            ("Dr. Sumudu Perera", "General Practitioner", 1),
            ("Dr. Nelum Kumari", "Family Medicine Specialist", 1),
            ("Dr. Sanjeewa Kumara", "Chief Cardiologist", 2),
            ("Dr. Harshani Silva", "Interventional Cardiologist", 2),
            ("Dr. Rohan Abeysekara", "Cardiovascular Surgeon", 2),
            ("Dr. Anoma Perera", "Senior Pediatrician", 3),
            ("Dr. Chamari Jayasinghe", "Neonatal Specialist", 3),
            ("Dr. Nihal Silva", "Neuro Surgeon", 4),
            ("Dr. Kithsiri Gunaratne", "Neurologist", 4),
            ("Dr. Deepani Fernando", "Clinical Neurologist", 4),
            ("Dr. K. Gunawardena", "Orthopedic Surgeon", 5),
            ("Dr. Tissa Rathnayake", "Joint Replacement Specialist", 5),
            ("Dr. Maheshi Fonseka", "Dermatologist", 6),
            ("Dr. Lakmal Edirisinghe", "Cosmetic Dermatologist", 6),
            ("Dr. S. K. Liyanage", "ENT Surgeon", 7),
            ("Dr. Nirosha Premaratne", "Otolaryngologist", 7)
        ]
        cursor.executemany("INSERT INTO doctors (name, specialty, dept_id) VALUES (?, ?, ?)", doctors_list)
        print("✅ Doctors seeded.")

    # C. Staff Accounts
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('admin', 'admin123', 'admin', 'System Admin')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role, fullname) VALUES ('doctor1', 'doc123', 'doctor', 'Dr. Perera')")

    db.commit()
    db.close()

# Initialize DB on startup
init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------
# ACCESS CONTROL
# ----------------------
def login_required(role=None):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return "Access Denied: Unauthorized Role", 403
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# ----------------------
# AUTH ROUTES
# ----------------------
@app.route("/")
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    role = session.get('role')
    if role == 'admin': return redirect(url_for('admin_dashboard'))
    if role == 'doctor': return redirect(url_for('doctor_schedule'))
    return redirect(url_for('home'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = (
            request.form["fullname"],
            request.form["address"],
            request.form["age"],
            request.form["phone"],
            request.form["email"],
            request.form["username"].strip(),
            request.form["password"].strip()
        )
        db = get_db()
        try:
            db.execute("""
                INSERT INTO users (fullname, address, age, phone, email, username, password, role) 
                VALUES (?, ?, ?, ?, ?, ?, ?, 'patient')
            """, data)
            db.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")
        finally:
            db.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        db.close()
        
        if not user:
            flash("Account not found. Please register.", "warning")
            return redirect(url_for('register'))
        
        if user['password'] == password:
            session.update({'user_id': user['id'], 'role': user['role'], 'username': user['username']})
            return redirect(url_for('index'))
        else:
            flash("Invalid password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------------
# PATIENT ROUTES
# ----------------------
@app.route("/home")
@login_required(role='patient')
def home():
    db = get_db()
    depts = db.execute("SELECT * FROM department").fetchall()
    db.close()
    return render_template("index.html", departments=depts)

@app.route("/book", methods=["POST"])
@login_required(role='patient')
def book():
    name = session['username']
    dept_id = request.form["department"]
    date = request.form["date"]
    time_str = request.form["time"]
    db = get_db()
    
    existing = db.execute("SELECT 1 FROM appointment WHERE department_id = ? AND appointment_date = ? AND appointment_time = ?", (dept_id, date, time_str)).fetchone()
    if existing:
        db.close()
        return jsonify({"status": "error", "message": "This slot is already booked. Please choose a slot at least 15 minutes later."}), 400

    ref_no = "HOSP-" + uuid.uuid4().hex[:8].upper()
    db.execute("INSERT INTO appointment (patient_name, department_id, appointment_date, appointment_time, reference_no) VALUES (?, ?, ?, ?, ?)", (name, dept_id, date, time_str, ref_no))
    db.commit()
    db.close()
    return jsonify({"status": "success", "reference_no": ref_no})

@app.route("/my_appointments")
@login_required(role='patient')
def my_appointments():
    db = get_db()
    # Pull appointments for the currently logged-in user only
    appointments = db.execute("""
        SELECT d.name AS department, a.appointment_date, a.appointment_time, a.reference_no 
        FROM appointment a JOIN department d ON a.department_id = d.id 
        WHERE LOWER(a.patient_name) = LOWER(?)
    """, (session['username'],)).fetchall()
    db.close()
    return render_template("my_appointments.html", appointments=appointments)

@app.route("/view_doctors")
@login_required()
def view_doctors():
    db = get_db()
    departments = db.execute("SELECT * FROM department").fetchall()
    hospital_staff = []
    for dept in departments:
        docs = db.execute("SELECT name, specialty FROM doctors WHERE dept_id = ?", (dept['id'],)).fetchall()
        if docs:
            hospital_staff.append({'dept_name': dept['name'], 'doctors': docs})
    db.close()
    return render_template("view_doctors.html", staff=hospital_staff)

# ----------------------
# ADMIN & DOCTOR ROUTES
# ----------------------
@app.route("/admin")
@login_required(role='admin')
def admin_dashboard():
    db = get_db()
    # You MUST select a.id so the delete button knows which row to remove
    query = """
        SELECT a.id, a.patient_name, d.name AS department, a.appointment_date, a.reference_no 
        FROM appointment a 
        JOIN department d ON a.department_id = d.id
    """
    appointments = db.execute(query).fetchall()
    total = len(appointments)
    db.close()
    return render_template("admin_dashboard.html", appointments=appointments, total=total)
    
@app.route("/admin/delete/<int:id>", methods=["POST"])
@login_required(role='admin')
def delete_appointment(id):
    db = get_db()
    db.execute("DELETE FROM appointment WHERE id = ?", (id,))
    db.commit()
    db.close()
    return jsonify({"status": "success"})

@app.route("/doctor/schedule")
@login_required(role='doctor')
def doctor_schedule():
    dept_id = request.args.get('dept_id', 1)
    db = get_db()
    departments = db.execute("SELECT * FROM department").fetchall()
    appointments = db.execute("SELECT patient_name, appointment_date, appointment_time FROM appointment WHERE department_id = ? ORDER BY appointment_date, appointment_time", (dept_id,)).fetchall()
    db.close()
    return render_template("doctor_schedule.html", appointments=appointments, departments=departments)

if __name__ == "__main__":
    app.run(debug=True)