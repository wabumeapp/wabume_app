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
from datetime import datetime

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import database.setup_db as setup_db
import psycopg2

app = Flask(__name__)
app.secret_key = "secretkey123"  # to encrypt the session 

@app.route("/")
def home():
    return redirect(url_for("wabume_info"))

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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(150) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        cur.execute("SELECT id FROM users WHERE username=%s", ("admin",))
        admin = cur.fetchone()

        if not admin:
            hashed_password = generate_password_hash("admin123")
            cur.execute("""
                INSERT INTO users (username, password, role, status)
                VALUES (%s, %s, %s, %s)
            """, ("admin", hashed_password, "admin", "active"))
            conn.commit()
            print("Admin account created ✅")

        cur.close()
        conn.close()

init_postgres()
create_admin_if_not_exists()

# ----------------- Wabume Info -----------------
@app.route("/wabume_info")
def wabume_info():
    return render_template("wabume_info.html")

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
                if status != "active":
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
    admin_code = request.form.get("admin_code", "").strip()

    CORRECT_ADMIN_CODE = "ADMIN123"

    # --- Get DB connection + placeholder ---
    conn, placeholder = get_db_connection()
    cursor = conn.cursor()

    if admin_code == CORRECT_ADMIN_CODE:
        # Retrieve the actual stored password (stored as plain text — not secure but acceptable for now)
        cursor.execute(f"SELECT password FROM users WHERE username ={placeholder}", (username,))
        r = cursor.fetchone()
        conn.close()

        if r:
            real_password = r[0]
            flash(f"Verified. Your password is: {real_password}", "success")
            return redirect(url_for("login"))
        else:
            # If user not found (rare case because frontend already validated it)
            flash("Account not found, please register.", "error")
            return redirect(url_for("signup"))
    else:
        # Wrong recovery code → treat as a new user and redirect to signup with countdown
        conn.close()
        return render_template("login.html", go_to_signup=True)

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
    accepted_users = cursor.fetchall()

    # New users only (pending)
    cursor.execute(f"SELECT id, username, created_at FROM users WHERE status='pending'")
    pending_users = cursor.fetchall()

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
    cursor.execute(f"SELECT username, status, created_at, recovery_code FROM users WHERE id={placeholder}", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        flash("User not found!", "error")
        return redirect(url_for("admin_dashboard"))

    username, status, created_at, recovery_code = user

    # Fetch user messages
    cursor.execute(f"SELECT date, time, phone, message FROM user_messages WHERE user_id={placeholder}", (user_id,))
    messages = cursor.fetchall()

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
        conn.close()
        flash("Your account has been rejected by the admin.", "error")
        return redirect(url_for("login"))

    # 🔹 Accepted
    if sent_msg == 0:
        # First login after acceptance → send recovery code message
        cursor.execute(f"UPDATE users SET sent_msg=1 WHERE id={placeholder}", (user_id,))
        conn.commit()
        conn.close()

        # Display page with recovery code and wait for user to take a screenshot
        return render_template("user_dashboard.html",
                               username=username,
                               status=status,
                               recovery_code=code
                               )
    else:
        # Any login after the first → run the program directly without showing any page
        conn.close()
        return redirect(url_for("download_app"))
 
# ----------------- Download App Page -----------------
@app.route("/download_app")
def download_app():
    if "role" not in session or session["role"] != "user":
        flash("Unauthorized access!", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # --- Get DB connection + placeholder ---
    conn, placeholder = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT username FROM users WHERE id={placeholder}", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("User not found!", "error")
        return redirect(url_for("login"))

    username = row[0]

    return render_template(
        "download_app.html",
        username=username
    )

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
        cursor.execute(f"SELECT created_at, username FROM users WHERE id ={placeholder}", (user_id,))
        row = cursor.fetchone()

        if row:
            created_at, username = row

            # Generate code from registration date
            raw = str(created_at)
            code = "".join([c for c in raw if c.isdigit()])  # 20251202051724349017

            # Update status + save code + set sent_msg=0
            cursor.execute(f"""
                UPDATE users 
                SET status='accepted', recovery_code={placeholder}, sent_msg=0
                WHERE id={placeholder}
            """, (code, user_id))
            conn.commit()
            conn.close()

        flash(f"{username} has been accepted.", "success")
        return redirect(url_for("admin_dashboard"))

    elif action == "reject":
        cursor.execute(f"SELECT username FROM users WHERE id={placeholder}", (user_id,))
        row = cursor.fetchone()
        username = row[0] if row else ""

        # Reject the user
        cursor.execute(f"UPDATE users SET status='rejected', sent_msg=0 WHERE id={placeholder}", (user_id,))
        conn.commit()
        conn.close()

        flash(f"{username} has been rejected.", "error")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    flash("Unexpected error.", "error")
    return redirect(url_for("admin_dashboard"))
    
# ----------------- Logout -----------------
@app.route("/logout")
def logout():
    session.clear()
    return render_template("login.html")

# ----------------- Run App -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)




