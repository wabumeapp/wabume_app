import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

# ----------------- إعداد المسار لقاعدة البيانات -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # نفس مسار هذا السكريبت
DB_PATH = os.path.join(BASE_DIR, "users.db")

# ----------------- إنشاء اتصال بالـ DB -----------------
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ----------------- إنشاء جدول المستخدمين إذا لم يكن موجود -----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL
)
""")

# ----------------- إنشاء حساب Admin افتراضي -----------------
admin_username = "admin"
admin_password = generate_password_hash("admin123")  # تشفير الباسورد

cursor.execute("""
INSERT OR IGNORE INTO users (username, password, role, status, created_at)
VALUES (?, ?, ?, ?, ?)
""", (admin_username, admin_password, "admin", "accepted", datetime.now()))

conn.commit()
conn.close()

print("Database created successfully! ✅")
print(f"Admin account -> Username: {admin_username} | Password: admin123")

# ----------------- إضافة عمود recovery_code لو مش موجود -----------------
DB_PATH = "database/users.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# إضافة recovery_code لو مش موجود
try:
    cursor.execute("ALTER TABLE users ADD COLUMN recovery_code TEXT")
except:
    pass

# إضافة sent_msg لو مش موجود (الأهم)
try:
    cursor.execute("ALTER TABLE users ADD COLUMN sent_msg INTEGER DEFAULT 0")
except:
    pass

conn.commit()
conn.close()

# ----------------- إضافة عمود sent_msg لو مش موجود -----------------
DB_PATH = "database/users.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN sent_msg INTEGER DEFAULT 0")
except:
    pass

conn.commit()
conn.close()


# ----------------- downloaded row -----------------
DB_PATH = "database/users.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN downloaded INTEGER DEFAULT 0")
except:
    pass

conn.commit()
conn.close()
