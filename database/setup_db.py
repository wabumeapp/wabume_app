import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

# -----------------  Set database path  -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))      # Same directory as this script
DB_PATH = os.path.join(BASE_DIR, "users.db")

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

# ----------------- Add recovery_code column if it doesn't exist -----------------
DB_PATH = "database/users.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN recovery_code TEXT")
except:
    pass

conn.commit()
conn.close()

# ----------------- Add sent_msg column again if needed -----------------
DB_PATH = "database/users.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN sent_msg INTEGER DEFAULT 0")
except:
    pass

conn.commit()
conn.close()

# ----------------- Add downloaded column if it doesn't exist -----------------
DB_PATH = "database/users.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN downloaded INTEGER DEFAULT 0")
except:
    pass

conn.commit()
conn.close()
