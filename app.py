from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "campusconnect_secret_key"

DATABASE = "campus_connect.db"


# ---------------- DATABASE CONNECTION ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- CREATE DATABASE ----------------

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            salary TEXT,
            skills TEXT,
            description TEXT,
            company_id INTEGER
        )
    """)

    # Internships table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            duration TEXT,
            stipend TEXT,
            skills TEXT,
            description TEXT,
            company_id INTEGER
        )
    """)

    # Applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            job_id INTEGER,
            internship_id INTEGER,
            status TEXT DEFAULT 'Pending',
            applied_date TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------- JOBS ----------------

@app.route("/jobs")
def jobs():

    search = request.args.get("search", "")
    location = request.args.get("location", "")
    skills = request.args.get("skills", "")

    conn = get_db()

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if search:
        query += " AND title LIKE ?"
        params.append("%" + search + "%")

    if location:
        query += " AND location LIKE ?"
        params.append("%" + location + "%")

    if skills:
        query += " AND skills LIKE ?"
        params.append("%" + skills + "%")

    query += " ORDER BY id DESC"

    jobs = conn.execute(query, params).fetchall()

    conn.close()

    return render_template(
        "jobs.html",
        jobs=jobs,
        search=search,
        location=location,
        skills=skills
    )
@app.route("/apply-job/<int:job_id>", methods=["POST"])
def apply_job(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "student":
        return "Only students can apply for jobs."

    student_id = session["user_id"]

    conn = get_db()

    # Check whether already applied
    existing = conn.execute("""
        SELECT * FROM applications
        WHERE student_id = ?
        AND job_id = ?
    """, (student_id, job_id)).fetchone()

    if existing:
        conn.close()
        return "You have already applied for this job."

    conn.execute("""
        INSERT INTO applications
        (student_id, job_id, internship_id, status, applied_date)
        VALUES (?, ?, NULL, 'Pending', ?)
    """, (
        student_id,
        job_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("student_dashboard"))
# ---------------- JOB DETAILS ----------------

@app.route("/job/<int:job_id>")
def job_details(job_id):

    conn = get_db()

    job = conn.execute("""
        SELECT * FROM jobs
        WHERE id = ?
    """, (job_id,)).fetchone()

    conn.close()

    if job is None:
        return "Job not found."

    return render_template(
        "job_details.html",
        job=job
    )

# ---------------- INTERNSHIPS ----------------

@app.route("/internship")
def internship():

    search = request.args.get("search", "")
    location = request.args.get("location", "")
    skills = request.args.get("skills", "")

    conn = get_db()

    query = "SELECT * FROM internships WHERE 1=1"
    params = []

    if search:
        query += " AND title LIKE ?"
        params.append("%" + search + "%")

    if location:
        query += " AND location LIKE ?"
        params.append("%" + location + "%")

    if skills:
        query += " AND skills LIKE ?"
        params.append("%" + skills + "%")

    query += " ORDER BY id DESC"

    internships = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return render_template(
        "internship.html",
        internships=internships,
        search=search,
        location=location,
        skills=skills
    )
@app.route("/apply-internship/<int:internship_id>", methods=["POST"])
def apply_internship(internship_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "student":
        return "Only students can apply for internships."

    student_id = session["user_id"]

    conn = get_db()

    existing = conn.execute("""
        SELECT * FROM applications
        WHERE student_id = ?
        AND internship_id = ?
    """, (student_id, internship_id)).fetchone()

    if existing:
        conn.close()
        return "You have already applied for this internship."

    conn.execute("""
        INSERT INTO applications
        (student_id, job_id, internship_id, status, applied_date)
        VALUES (?, NULL, ?, 'Pending', ?)
    """, (
        student_id,
        internship_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("student_dashboard"))
@app.route("/admin/delete-internship/<int:internship_id>",
           methods=["POST"])
def delete_internship(internship_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "Access denied."

    conn = get_db()

    conn.execute("""
        DELETE FROM applications
        WHERE internship_id = ?
    """, (internship_id,))

    conn.execute("""
        DELETE FROM internships
        WHERE id = ?
    """, (internship_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))
# ---------------- INTERNSHIP DETAILS ----------------

@app.route("/internship/<int:internship_id>")
def internship_details(internship_id):

    conn = get_db()

    internship = conn.execute("""
        SELECT * FROM internships
        WHERE id = ?
    """, (internship_id,)).fetchone()

    conn.close()

    if internship is None:
        return "Internship not found."

    return render_template(
        "internship_details.html",
        internship=internship
    )
# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirmPassword"]
        role = request.form["role"]

        # Check password
        if password != confirm_password:
            return "Passwords do not match!"

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, password, role)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                password,
                role
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return "Email already registered!"

        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email = ?
            AND password = ?
            AND role = ?
        """, (email, password, role)).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]

            if role == "student":
                return redirect(url_for("student_dashboard"))

            elif role == "company":
                return redirect(url_for("company_dashboard"))

            elif role == "admin":
                return redirect(url_for("admin_dashboard"))

        return "Invalid email, password or role!"

    return render_template("login.html")
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))

# ---------------- STUDENT DASHBOARD ----------------

@app.route("/student-dashboard")
def student_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "student":
        return "Access denied."

    student_id = session["user_id"]

    conn = get_db()

    applications = conn.execute("""
        SELECT
            applications.*,
            jobs.title AS job_title,
            jobs.company AS job_company,
            internships.title AS internship_title,
            internships.company AS internship_company

        FROM applications

        LEFT JOIN jobs
        ON applications.job_id = jobs.id

        LEFT JOIN internships
        ON applications.internship_id = internships.id

        WHERE applications.student_id = ?

        ORDER BY applications.id DESC
    """, (student_id,)).fetchall()

    # Make company field available for both jobs and internships
    application_list = []

    for application in applications:

        data = dict(application)

        if data["job_title"]:
            data["company"] = data["job_company"]
        else:
            data["company"] = data["internship_company"]

        application_list.append(data)

    conn.close()

    return render_template(
        "student_dashboard.html",
        applications=application_list,
        user_name=session["user_name"]
    )


# ---------------- COMPANY DASHBOARD ----------------

# ---------------- COMPANY DASHBOARD ----------------

@app.route("/company-dashboard")
def company_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "company":
        return "Access denied."

    return render_template("company_dashboard.html")

# ---------------- COMPANY APPLICATIONS ----------------

@app.route("/company-applications")
def company_applications():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "company":
        return "Access denied."

    company_id = session["user_id"]

    conn = get_db()

    applications = conn.execute("""
        SELECT
            applications.id,
            applications.status,
            applications.applied_date,

            users.name AS student_name,
            users.email AS student_email,

            jobs.title AS job_title,
            jobs.company AS job_company,

            internships.title AS internship_title,
            internships.company AS internship_company

        FROM applications

        JOIN users
        ON applications.student_id = users.id

        LEFT JOIN jobs
        ON applications.job_id = jobs.id

        LEFT JOIN internships
        ON applications.internship_id = internships.id

        WHERE jobs.company_id = ?
           OR internships.company_id = ?

        ORDER BY applications.id DESC

    """, (company_id, company_id)).fetchall()

    conn.close()

    return render_template(
        "company_applications.html",
        applications=applications
    )
# ---------------- UPDATE APPLICATION STATUS ----------------

@app.route("/update-application/<int:application_id>/<status>",
           methods=["POST"])
def update_application(application_id, status):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "company":
        return "Access denied."

    if status not in ["Accepted", "Rejected"]:
        return "Invalid status."

    conn = get_db()

    conn.execute("""
        UPDATE applications
        SET status = ?
        WHERE id = ?
    """, (status, application_id))

    conn.commit()
    conn.close()

    return redirect(url_for("company_applications"))

# ---------------- CHECK USERS ----------------

@app.route("/check-users")
def check_users():

    conn = get_db()

    users = conn.execute(
        "SELECT id, name, email, role FROM users"
    ).fetchall()

    conn.close()

    return render_template(
        "check_users.html",
        users=users
    )
# ---------------- POST JOB ----------------

# ---------------- POST JOB ----------------

@app.route("/post-job", methods=["GET", "POST"])
def post_job():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "company":
        return "Access denied."

    if request.method == "POST":

        title = request.form["title"]
        company = request.form["company"]
        location = request.form["location"]
        salary = request.form["salary"]
        skills = request.form["skills"]
        description = request.form["description"]

        company_id = session["user_id"]

        conn = get_db()

        conn.execute("""
            INSERT INTO jobs
            (title, company, location, salary, skills, description, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            company,
            location,
            salary,
            skills,
            description,
            company_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("jobs"))

    return render_template("post_job.html")

# ---------------- POST INTERNSHIP ----------------

@app.route("/post-internship", methods=["GET", "POST"])
def post_internship():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "company":
        return "Access denied."

    if request.method == "POST":

        title = request.form["title"]
        company = request.form["company"]
        location = request.form["location"]
        duration = request.form["duration"]
        stipend = request.form["stipend"]
        skills = request.form["skills"]
        description = request.form["description"]

        company_id = session["user_id"]

        conn = get_db()

        conn.execute("""
            INSERT INTO internships
            (title, company, location, duration,
             stipend, skills, description, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            company,
            location,
            duration,
            stipend,
            skills,
            description,
            company_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("internships"))

    return render_template("post_internship.html")

# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin-dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "Access denied."

    conn = get_db()

    students = conn.execute("""
        SELECT * FROM users
        WHERE role = 'student'
        ORDER BY id DESC
    """).fetchall()

    companies = conn.execute("""
        SELECT * FROM users
        WHERE role = 'company'
        ORDER BY id DESC
    """).fetchall()

    jobs = conn.execute("""
        SELECT * FROM jobs
        ORDER BY id DESC
    """).fetchall()

    internships = conn.execute("""
        SELECT * FROM internships
        ORDER BY id DESC
    """).fetchall()

    applications = conn.execute("""
        SELECT
            applications.*,
            users.name AS student_name,
            users.email AS student_email,
            jobs.title AS job_title,
            internships.title AS internship_title

        FROM applications

        JOIN users
        ON applications.student_id = users.id

        LEFT JOIN jobs
        ON applications.job_id = jobs.id

        LEFT JOIN internships
        ON applications.internship_id = internships.id

        ORDER BY applications.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        students=students,
        companies=companies,
        jobs=jobs,
        internships=internships,
        applications=applications
    )
@app.route("/admin/delete-job/<int:job_id>", methods=["POST"])
def delete_job(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "Access denied."

    conn = get_db()

    # Delete related applications first
    conn.execute("""
        DELETE FROM applications
        WHERE job_id = ?
    """, (job_id,))

    conn.execute("""
        DELETE FROM jobs
        WHERE id = ?
    """, (job_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":

    init_db()

app.run(host="10.66.31.214", port=8080, debug=True, use_reloader=True, use_debugger=False)