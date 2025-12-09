from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import request, render_template, redirect, url_for, flash, session
from flask import send_from_directory
import sqlite3
import subprocess, threading, time
from datetime import datetime
import os
import subprocess

app = Flask(__name__)
app.secret_key = "secretkey123"  # لتشفير session

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

# ----------------- Signup -----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if username == "" or password == "":
            flash("Please fill in all fields.", "error")   #الرجاء ملء جميع الحقول
            return redirect(url_for("signup"))

        conn = sqlite3.connect("database/users.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        exists = cursor.fetchone()

        if exists:
            conn.close()
            flash("Username already exists!", "success")    #اسم المستخدم موجود مسبقاً
            return render_template("signup.html", username_exists=True)
        
        
        # تحقق من وجود الاسم فقط
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        exists_name = cursor.fetchone()

        if exists_name:
            conn.close()
            flash("الاسم مستخدم من قبل، الرجاء اختيار اسم آخر.", "error")
            return render_template("signup.html")

        cursor.execute("""
            INSERT INTO users (username, password, role, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password, "user", "pending", datetime.now()))

        conn.commit()
        conn.close()
        flash("You have successfully registered! Waiting for admin approval.", "success")   #تم تسجيلك بنجاح! في انتظار موافقة الادمن
        return redirect(url_for("signup"))  # ⚡ يبقى على الصفحة نفسها

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
                    flash("لم يتم اعتماد حسابك بعد.", "info")
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
            flash("حساب غير موجود، يرجى التسجيل أولاً.", "error")
            return redirect(url_for("signup"))

    return render_template("login.html")

# ----------------- Recover -----------------
# استجابة لكود الاسترجاع (POST من القالب recoverForm)
@app.route("/recover", methods=["POST"])
def recover():
    username = request.form.get("username")
    admin_code = request.form.get("admin_code", "").strip()

    # تحقق من الكود - هنا مثال بسيط: الكود الصحيح "ADMIN123"
    # الأفضل: خزن كود لكل مستخدم في DB و/أو استخدم OTP عبر email/phone
    CORRECT_ADMIN_CODE = "ADMIN123"

    if admin_code == CORRECT_ADMIN_CODE:
        # استخرج كلمة المرور الحقيقية (مخزن نصي — غير آمن لكن عملي الآن)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        r = cursor.fetchone()
        conn.close()
        if r:
            real_password = r[0]
            flash(f"تم التحقق. كلمة مرورك: {real_password}", "success")
            return redirect(url_for("login"))
        else:
            # لو ما لقينا المستخدم (نادر لأن frontend مرره)
            flash("حساب غير موجود، يرجى التسجيل.", "error")
            return redirect(url_for("signup"))
    else:
        # كود غلط -> نعتبره شخص جديد ونوجّهه للتسجيل بعد countdown
        return render_template("login.html", go_to_signup=True)

# ----------------- Admin Dashboard -----------------
@app.route("/admin")
def admin_dashboard():
    if "role" not in session or session["role"] != "admin":
        flash("غير مصرح بالدخول!", "error")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # المستخدمين المقبولين فقط
    cursor.execute("SELECT id, username, role, status, created_at FROM users WHERE status='accepted'")
    accepted_users = cursor.fetchall()


    # المستخدمين الجدد فقط (pending)
    cursor.execute("SELECT id, username, created_at FROM users WHERE status='pending'")
    pending_users = cursor.fetchall()

    conn.close()
    return render_template("admin_dashboard.html", accepted_users=accepted_users, pending_users=pending_users)

# ----------------- Details -----------------
@app.route("/user/<int:user_id>")
def user_details(user_id):
    if "role" not in session or session["role"] != "admin":
        flash("غير مصرح بالدخول!", "error")
        return redirect(url_for("login"))

    # جلب بيانات المستخدم من DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, status, created_at, recovery_code FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        flash("المستخدم غير موجود!", "error")
        return redirect(url_for("admin_dashboard"))

    username, status, created_at, recovery_code = user
    # الرسائل: لو بدك نربط البرنامج القديم هنا
    # مثال: بتقدر ترسل قائمة رسائل من البرنامج القديم بدل txt
    messages = []  # لاحقاً بنربط البرنامج القديم هنا

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
        flash("غير مصرح بالدخول!", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, status, recovery_code, sent_msg FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        flash("المستخدم غير موجود!", "error")
        return redirect(url_for("login"))

    username, status, code, sent_msg = row

    script_path = os.path.join("automation", "wabume.py")

    if status == "pending":
        conn.close()
        return render_template("user_dashboard.html", username=username, status=status)

    if status == "rejected":
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        flash("تم رفض حسابك من قبل الإدارة.", "error")
        return redirect(url_for("login"))

    # status == accepted
    if sent_msg == 0:
        # أول login بعد accept → أرسل رسالة الكود
        cursor.execute("UPDATE users SET sent_msg=1 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()

        # دالة لتشغيل البرنامج بعد 10 ثواني
        def run_script():
            time.sleep(10)
            subprocess.Popen(["python", script_path])

        threading.Thread(target=run_script).start()

        # عرض صفحة بها الكود وانتظار المستخدم لعمل SS
        return render_template("user_dashboard.html",
                               username=username,
                               status=status,
                               recovery_code=code)

    else:
        # أي login بعد الأول → فتح البرنامج مباشرة بدون أي صفحة
        conn.close()
        subprocess.Popen(["python", script_path])
        return "", 204  # لا تعرض أي HTML


# ----------------- Admin Accept / Reject -----------------
@app.route("/admin_action", methods=["POST"])
def admin_action():
    if "role" not in session or session["role"] != "admin":
        flash("غير مصرح بالدخول!", "error")
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

            # إنشاء الكود من التاريخ
            raw = str(created_at)
            code = "".join([c for c in raw if c.isdigit()])  # 20251202051724349017

            # تحديث الحالة + حفظ الكود + sent_msg=0
            cursor.execute("""
                UPDATE users 
                SET status='accepted', recovery_code=?, sent_msg=0
                WHERE id=?
            """, (code, user_id))
            conn.commit()
            conn.close()

            flash(f"تم قبول {username}.", "success")
            return redirect(url_for("admin_dashboard"))

    elif action == "reject":
        cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
        row = cursor.fetchone()
        username = row[0] if row else ""

        # رفض المستخدم
        cursor.execute("UPDATE users SET status='rejected', sent_msg=0 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()

        flash(f"تم رفض {username}.", "info")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    flash("خطأ غير متوقع.", "error")
    return redirect(url_for("admin_dashboard"))
    
# ----------------- Logout -----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("تم تسجيل الخروج.", "info")
    return redirect(url_for("login"))


# ----------------- Run App -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)