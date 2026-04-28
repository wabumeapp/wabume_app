from flask import Flask, request, jsonify
import sqlite3
import uuid
from datetime import datetime
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "database", "users.db")

def get_db():
    return sqlite3.connect(DB, check_same_thread=False)

# 🔐 LOGIN via recovery_code
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    
    if not data:
        return {"success": False}
    
    recovery_code = data["recovery_code"]
    device_id = data["device_id"]

    conn = get_db()
    cursor = conn.cursor()

    # 🔥 1. تحقق من users (مش sessions)
    cursor.execute("SELECT id FROM users WHERE recovery_code = ?", (recovery_code,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return {"success": False, "error": "Invalid recovery code"}

    # 🔍 2. check user exists in sessions
    cursor.execute("SELECT active_session_id FROM sessions WHERE recovery_code = ?", (recovery_code,))
    row = cursor.fetchone()

    session_id = str(uuid.uuid4())

    if row:
        # update existing
        cursor.execute("""
            UPDATE sessions
            SET active_session_id = ?, device_id = ?, last_seen = ?
            WHERE recovery_code = ?
        """, (session_id, device_id, datetime.now(), recovery_code))
    else:
        # first time insert
        cursor.execute("""
            INSERT INTO sessions (recovery_code, active_session_id, device_id, last_seen)
            VALUES (?, ?, ?, ?)
        """, (recovery_code, session_id, device_id, datetime.now()))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "session_id": session_id
    }


# ❤️ heartbeat
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json(silent=True)
    if not data:
        return {"success": False}
    
    recovery_code = data["recovery_code"]
    session_id = data["session_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT active_session_id FROM sessions WHERE recovery_code = ?
    """, (recovery_code,))
    row = cursor.fetchone()

    if not row:
        return {"valid": False}

    if row[0] != session_id:
        return {"valid": False}

    cursor.execute("""
        UPDATE sessions SET last_seen = ? WHERE recovery_code = ?
    """, (datetime.now(), recovery_code))

    conn.commit()
    conn.close()

    return {"valid": True}

app.run(host="0.0.0.0", port=5000)