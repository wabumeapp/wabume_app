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
import sqlite3
from datetime import datetime
import os
import subprocess

app = Flask(__name__)
app.secret_key = "secretkey123"  # to encrypt the session 

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route('/google13f31b5e24964739.html')
def google_verify():
    return send_from_directory('.', 'google13f31b5e24964739.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

DB_PATH = "database/users.db"
if not os.path.exists(DB_PATH):
    subprocess.run(["python", "database/setup_db.py"])

# ----------------- Signup -----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if username == "" or password == "":
            flash("Please fill in all fields.", "error")
            return redirect(url_for("signup"))

        conn = sqlite3.connect("database/users.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        exists = cursor.fetchone()

        if exists:
            conn.close()
            flash("Username already exists!", "success")   
            return render_template("signup.html", username_exists=True)
        
        
        # Check if the username exists only
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        exists_name = cursor.fetchone()

        if exists_name:
            conn.close()
            flash("Username already taken, please choose another.", "error")
            return render_template("signup.html")

        cursor.execute("""
            INSERT INTO users (username, password, role, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password, "user", "pending", datetime.now()))

        conn.commit()
        conn.close()
        flash("You have successfully registered! Waiting for admin approval.", "success")   #تم تسجيلك بنجاح! في انتظار موافقة الادمن
        return redirect(url_for("signup"))  # ⚡ Stay on the same page

    return render_template("signup.html")

# ----------------- Login -----------------
DB_PATH = "database/users.db"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role, status FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row:
            user_id, real_password, role, status = row
            if password == real_password:
                if status != "accepted":
                    flash("Your account has not been approved yet.", "info")
                    return redirect(url_for("login"))
                # login success
                session["user_id"] = user_id
                session["role"] = role

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

    if admin_code == CORRECT_ADMIN_CODE:
        # Retrieve the actual stored password (stored as plain text — not secure but acceptable for now)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
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
        return render_template("login.html", go_to_signup=True)

# ----------------- Admin Dashboard -----------------
@app.route("/admin")
def admin_dashboard():
    if "role" not in session or session["role"] != "admin":
        flash("Access denied!", "error")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Accepted users only
    cursor.execute("SELECT id, username, role, status, created_at FROM users WHERE status='accepted'")
    accepted_users = cursor.fetchall()

    # New users only (pending)
    cursor.execute("SELECT id, username, created_at FROM users WHERE status='pending'")
    pending_users = cursor.fetchall()

    conn.close()
    return render_template("admin_dashboard.html", accepted_users=accepted_users, pending_users=pending_users)

# ----------------- Details -----------------
@app.route("/user/<int:user_id>")
def user_details(user_id):
    if "role" not in session or session["role"] != "admin":
        flash("Unauthorized access!", "error")
        return redirect(url_for("login"))

    # Fetch user data from DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, status, created_at, recovery_code FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        flash("User not found!", "error")
        return redirect(url_for("admin_dashboard"))

    username, status, created_at, recovery_code = user
     
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT date, time, phone, message FROM user_messages WHERE user_id=?", (user_id,))
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

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, status, recovery_code, sent_msg FROM users WHERE id=?", (user_id,))
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
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        flash("Your account has been rejected by the admin.", "error")
        return redirect(url_for("login"))

    # 🔹 Accepted
    if sent_msg == 0:
        # First login after acceptance → send recovery code message
        cursor.execute("UPDATE users SET sent_msg=1 WHERE id=?", (user_id,))
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
        return redirect(url_for("download_page"))

# ----------------- Download Page -----------------
@app.route("/download")
def download_page():
    if "role" not in session or session["role"] != "user":
        flash("Unauthorized access!", "error")
        return redirect(url_for("login"))

    filename = "wabume.exe"   # أو wabume.zip

    return render_template(
        "download.html",
        username=session.get("username"),
        file_name=filename
    )

# ----------------- Serve Download -----------------
@app.route("/download_file/<filename>")
def download_file(filename):
    downloads_folder = os.path.join(app.root_path, "static", "files")
    return send_from_directory(
        directory=downloads_folder,
        filename=filename,
        as_attachment=True
    )

# ----------------- Admin Accept / Reject -----------------
@app.route("/admin_action", methods=["POST"])
def admin_action():
    if "role" not in session or session["role"] != "admin":
        flash("Unauthorized access!", "error")
        return redirect(url_for("login"))

    user_id = request.form.get("user_id")
    action = request.form.get("action")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if action == "accept":
        cursor.execute("SELECT created_at, username FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            created_at, username = row

            # Generate code from registration date
            raw = str(created_at)
            code = "".join([c for c in raw if c.isdigit()])  # 20251202051724349017

            # Update status + save code + set sent_msg=0
            cursor.execute("""
                UPDATE users 
                SET status='accepted', recovery_code=?, sent_msg=0
                WHERE id=?
            """, (code, user_id))
            conn.commit()
            conn.close()

        flash(f"{username} has been accepted.", "success")
        return redirect(url_for("admin_dashboard"))

    elif action == "reject":
        cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
        row = cursor.fetchone()
        username = row[0] if row else ""

        # Reject the user
        cursor.execute("UPDATE users SET status='rejected', sent_msg=0 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()

        flash(f"{username} has been rejected.", "info")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    flash("Unexpected error.", "error")
    return redirect(url_for("admin_dashboard"))
    
# ----------------- Logout -----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


# ----------------- Run App -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)