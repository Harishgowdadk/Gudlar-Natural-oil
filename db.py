import os
import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash


def get_connection():
    """
    Open a fresh connection to the MySQL database running under XAMPP.
    Each request should grab its own connection and close it when done
    (see app.py's teardown handler).
    """
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "gudlar_db"),
        cursorclass=DictCursor,
        autocommit=True,
    )


def ensure_default_admin():
    """
    Create a default admin account (admin / admin123) the very first time
    the app starts, so there is no manual password-hashing step needed.
    Safe to call on every startup -- it only inserts when the table is empty.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM admins LIMIT 1")
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO admins (username, password) VALUES (%s, %s)",
                    ("admin", generate_password_hash("admin123")),
                )
    finally:
        conn.close()


def ensure_users_table():
    """Creates the customers table if you imported an older gudlar.sql."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  full_name VARCHAR(100) NOT NULL,
                  email VARCHAR(120) NOT NULL UNIQUE,
                  phone VARCHAR(10) NOT NULL,
                  password VARCHAR(255) NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
            """)
    finally:
        conn.close()
