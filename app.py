from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory
)
import os
import sqlite3
import re
from datetime import datetime

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import database.setup_db as setup_db
import psycopg2

import uuid

app = Flask(__name__)
app.secret_key = "secretkey123"  # to encrypt the session 

@app.route("/")
def home():
    return redirect(url_for("info"))

@app.route('/google13f31b5e24964739.html')
def google_verify():
    return send_from_directory('.', 'google13f31b5e24964739.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

# --- Setup local database ---
DB_PATH = "database/users.db"
os.makedirs("database", exist_ok=True)

# Create DB only once if it doesn't exist
if not os.path.exists(DB_PATH):
    setup_db.create_db(DB_PATH)

# --- Flexible DB connection (PostgreSQL or SQLite) ---
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Must manually commit for PostgreSQL
        placeholder = "%s"
        return conn, placeholder
    else:
        conn = sqlite3.connect(DB_PATH)
        placeholder = "?"
        return conn, placeholder
    
def init_postgres():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # ---------------- USERS ----------------
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                username VARCHAR(150) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                status VARCHAR(50) DEFAULT 'pending',
                recovery_code TEXT,
                sent_msg INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # ---------------- SESSIONS ----------------
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                recovery_code TEXT PRIMARY KEY,
                active_session_id TEXT,
                device_id TEXT,
                last_seen TIMESTAMP
            );
        """)

        # ---------------- USER MESSAGES ----------------
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_messages (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT,
                date TEXT,
                time TEXT,
                phone TEXT,
                message TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("PostgreSQL table ready ✅")

def create_admin_if_not_exists():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # check if admin exists
        cur.execute("SELECT id FROM users WHERE username=%s", ("admin",))
        admin = cur.fetchone()

        if not admin:
            admin_username = "admin"
            admin_password = "admin123"
            admin_password_hash = generate_password_hash(admin_password)
            admin_recovery = "ADMIN123"

            cur.execute("""
                INSERT INTO users (username, password, role, status, recovery_code, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                admin_username, 
                admin_password_hash, 
                "admin", 
                "accepted", 
                admin_recovery, 
                datetime.now()
            ))
            
            conn.commit()
            print("Admin account created ✅")

        cur.close()
        conn.close()

init_postgres()
create_admin_if_not_exists()

def show_sqlite_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users);")
    columns = cursor.fetchall()
    print("SQLite columns:")
    for col in columns:
        print(col)
    conn.close()

show_sqlite_columns()

# ----------------- Wabume Info -----------------
@app.route("/info")
def info():
    return render_template("info.html")

# ----------------- Signup -----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if username == "" or password == "":
            flash("Please fill in all fields.", "error")
            return redirect(url_for("signup"))

        # --- Get DB connection + placeholder ---
        conn, placeholder = get_db_connection()
        cursor = conn.cursor()

        # Check if username exists
        cursor.execute(f"SELECT id FROM users WHERE username ={placeholder}", (username,))
        exists = cursor.fetchone()

        if exists:
            conn.close()
            flash("Username already exists!", "info")   
            return render_template("signup.html", username_exists=True)

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Insert new user
        cursor.execute(f"""
            INSERT INTO users (username, password, role, status, created_at)
            VALUES ({placeholder}, {placeholder}, 'user', 'pending', {placeholder})
        """, (username, hashed_password, datetime.now()))

        conn.commit()
        conn.close()

        flash("You have successfully registered! Waiting for admin approval.", "success")  
        return redirect(url_for("signup"))  # ⚡ Stay on the same page

    return render_template("signup.html")

# ----------------- Login -----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        # --- Get DB connection + placeholder ---
        conn, placeholder = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(f"SELECT id, password, role, status FROM users WHERE username ={placeholder}", (username,))
        row = cursor.fetchone()
        conn.close()

        if row:
            user_id, real_password, role, status = row

            if check_password_hash(real_password, password):
                if status != "accepted":
                    flash("Your account has not been approved yet.", "info")
                    return redirect(url_for("login"))
                
                # login success
                session["user_id"] = user_id
                session["role"] = role
                session["username"] = username 

                if role == "admin":
                    return redirect(url_for("admin_dashboard"))
                else:
                    return redirect(url_for("user_dashboard"))
                
            else:
                # username exists but password wrong -> show radios + recovery input
                return render_template("login.html",
                                       password_wrong=True,
                                       user_exists=True,
                                       attempted_username=username)
        else:
            flash("Account not found, please register first.", "error")
            return redirect(url_for("signup"))

    return render_template("login.html")

# ----------------- Recover -----------------
@app.route("/recover", methods=["POST"])
def recover():
    username = request.form.get("username")
    code = request.form.get("thecode", "").strip()

    # --- Get DB connection + placeholder ---
    conn, placeholder = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT recovery_code FROM users WHERE username ={placeholder}", (username,))
    row = cursor.fetchone()

    if row and row[0] == code:
        # ✅ بدل ما نرجع الباسورد → نحوّل لصفحة reset
        session["reset_user"] = username

        cursor.close()
        conn.close()

        return redirect(url_for("reset_password"))
    
    else:
        # Wrong recovery code → treat as a new user and redirect to signup with countdown
        cursor.close()
        conn.close()
        return render_template("login.html", go_to_signup=True)

# ----------------- Reset Password -----------------
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if "reset_user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if new_password == "" or confirm_password == "":
            flash("All fields are required*", "error")
            return redirect(url_for("reset_password"))
        
        if len(new_password) < 6:
            flash("Password must be at least 6 characters", "error")
            return redirect(url_for("reset_password"))
        
        if not re.search(r"[0-9]", new_password):
            flash("Must contain at least one number", "error")
        
        if not re.search(r"[A-Za-z]", new_password):
            flash("Must contain at least one letter", "error")
            return redirect(url_for("reset_password"))

        if new_password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("reset_password"))
        
        conn, placeholder = get_db_connection()
        cursor = conn.cursor()

        hashed = generate_password_hash(new_password)

        cursor.execute(
            f"UPDATE users SET password={placeholder} WHERE username={placeholder}",
            (hashed, session["reset_user"])
        )

        conn.commit()

        cursor.close()
        conn.close()

        session.pop("reset_user")

        flash("Password updated successfully!", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

# ----------------- Admin Dashboard -----------------
@app.route("/admin")
def admin_dashboard():
    if "role" not in session or session["role"] != "admin":
        flash("Access denied!", "error")
        return redirect(url_for("login"))

    # --- Get DB connection + placeholder ---
    conn, placeholder = get_db_connection()
    cursor = conn.cursor()

    # Accepted users only
    cursor.execute(f"SELECT id, username, role, status, created_at FROM users WHERE status='accepted'")

    accepted_users = [
        {"id": u[0], "username": u[1], "role": u[2], "status": u[3], "created_at": u[4]}
        for u in cursor.fetchall()
    ]

    # New users only (pending)
    cursor.execute(f"SELECT id, username, created_at FROM users WHERE status='pending'")

    pending_users = [
        {"id": u[0], "username": u[1], "created_at": u[2]}
        for u in cursor.fetchall()
    ]

    cursor.close()
    conn.close()
    return render_template("admin_dashboard.html", accepted_users=accepted_users, pending_users=pending_users)

# ----------------- Details -----------------
@app.route("/user_details/<int:user_id>")
def user_details(user_id):
    if "role" not in session or session["role"] != "admin":
        flash("Unauthorized access!", "error")
        return redirect(url_for("login"))

    # --- Get DB connection + placeholder ---
    conn, placeholder = get_db_connection()
    cursor = conn.cursor()

    # Fetch user data
    cursor.execute(f"SELECT username, status, recovery_code, created_at FROM users WHERE id={placeholder}", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        flash("User not found!", "error")
        return redirect(url_for("admin_dashboard"))

    username, status, created_at, recovery_code = user

    # Fetch user messages
    cursor.execute(f"SELECT date, time, phone, message FROM user_messages WHERE user_id={placeholder}", (user_id,))

    messages = [
        {
            "date": m[0],
            "time": m[1],
            "phone": m[2],
            "message": m[3]
        }
        for m in cursor.fetchall()
    ]

    cursor.close()
    conn.close()


    # Messages: later we can link the old program here
    # Example: you can send a list of messages from the old program instead of a txt file
    # messages = []  # Will link the old program here later

    return render_template("user_details.html",
                           username=username,
                           status=status,
                           created_at=created_at,
                           recovery_code=recovery_code,
                           messages=messages)

# ----------------- User Dashboard -----------------
@app.route("/user")
def user_dashboard():
    if "role" not in session or session["role"] != "user":
        flash("Unauthorized access!", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # --- Get DB connection + placeholder ---
    conn, placeholder = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT username, status, recovery_code, sent_msg FROM users WHERE id={placeholder}", (user_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        flash("User not found!", "error")
        return redirect(url_for("login"))

    username, status, code, sent_msg = row

    # 🔹 Pending
    if status == "pending":
        conn.close()
        return render_template("user_dashboard.html", username=username, status=status)

    # 🔹 Rejected
    if status == "rejected":
        cursor.execute(f"DELETE FROM users WHERE id={placeholder}", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Your account has been rejected by the admin.", "error")
        return redirect(url_for("login"))

    # 🔹 Accepted
    if sent_msg == 0:
        # First login after acceptance → send recovery code message
        cursor.execute(f"UPDATE users SET sent_msg=1 WHERE id={placeholder}", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()

        # Display page with recovery code and wait for user to take a screenshot
        return render_template("user_dashboard.html",
                               username=username,
                               status=status,
                               recovery_code=code
                               )
    else:
        # Any login after the first → run the program directly without showing any page
        cursor.close()
        conn.close()
        return redirect(url_for("run"))
 
# ----------------- Running Page -----------------
@app.route("/run")
def run():
    if "role" not in session or session["role"] != "user":
        flash("Unauthorized access!", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # --- Get DB connection + placeholder ---
    conn, placeholder = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT username FROM users WHERE id={placeholder}", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        flash("User not found!", "error")
        return redirect(url_for("login"))

    username = row[0]

    return render_template("run.html",username=username)

# ----------------- Admin Accept / Reject -----------------
@app.route("/admin_action", methods=["POST"])
def admin_action():
    if "role" not in session or session["role"] != "admin":
        flash("Unauthorized access!", "error")
        return redirect(url_for("login"))

    user_id = request.form.get("user_id")
    action = request.form.get("action")

    # --- Get DB connection + placeholder ---
    conn, placeholder = get_db_connection()
    cursor = conn.cursor()

    if action == "accept":
        cursor.execute(f"SELECT username FROM users WHERE id ={placeholder}", (user_id,))
        row = cursor.fetchone()

        if row:
            username = row[0]

            # Generate code 
            code = uuid.uuid4().hex[:8].upper()  

            # Update status + save code + set sent_msg=0
            cursor.execute(f"""
                UPDATE users 
                SET status='accepted', recovery_code={placeholder}, sent_msg=0
                WHERE id={placeholder}
            """, (code, user_id))
            conn.commit()
            cursor.close()
            conn.close()

        flash(f"{username} has been accepted.", "success")
        return redirect(url_for("admin_dashboard"))

    elif action == "reject":
        cursor.execute(f"SELECT username FROM users WHERE id={placeholder}", (user_id,))
        row = cursor.fetchone()
        username = row[0] if row else ""

        # Reject the user
        cursor.execute(f"UPDATE users SET status='rejected', recovery_code=NULL, sent_msg=0 WHERE id={placeholder}", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()

        flash(f"{username} has been rejected.", "error")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    flash("Unexpected error.", "error")
    return redirect(url_for("admin_dashboard"))

# ----------------- Wabume Page -----------------

# ----------------- Logout -----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return render_template("login.html")

# ----------------- Run App -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)




