import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

# -----------------  Set database path  -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))      # Same directory as this script
DB_PATH = os.path.join(BASE_DIR, "users.db")

# ----------------- Ensure folder exists -----------------
os.makedirs(BASE_DIR, exist_ok=True)

# ----------------- Connect to the DB -----------------
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ----------------- Create users table if it doesn't exist -----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    status TEXT NOT NULL DEFAULT 'pending',
    recovery_code TEXT,
    sent_msg INTEGER DEFAULT 0,
    downloaded INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL
)
""")

# ----------------- Create default Admin account -----------------
admin_username = "admin"
admin_password = "admin123"
admin_password_hash = generate_password_hash(admin_password)  # Encrypt password

cursor.execute("""
INSERT OR IGNORE INTO users (username, password, role, status, created_at)
VALUES (?, ?, ?, ?, ?)
""", (admin_username, admin_password_hash, "admin", "accepted", datetime.now()))

conn.commit()
conn.close()

print("Database created successfully! ✅")
print(f"Admin account -> Username: {admin_username} | Password: {admin_password} ")
