import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

def create_db(db_path):
    # Connect to DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Users table
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

    # User messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        time TEXT,
        phone TEXT,
        message TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Default admin
    admin_username = "admin"
    admin_password = "admin123"
    admin_password_hash = generate_password_hash(admin_password)

    cursor.execute("""
    INSERT OR IGNORE INTO users (username, password, role, status, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (admin_username, admin_password_hash, "admin", "accepted", datetime.now()))

    conn.commit()
    conn.close()
    print("Database ready ✅")
    print(f"Admin account -> Username: {admin_username} | Password: {admin_password}")

# Only run if executed directly
if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "users.db")
    create_db(DB_PATH)
