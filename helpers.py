import re
from functools import wraps

from flask import redirect, url_for, flash, request
from flask_login import UserMixin, current_user

from db import get_connection

PHONE_RE = re.compile(r"^[6-9][0-9]{9}$")


def valid_phone(phone):
    return bool(PHONE_RE.match(phone or ""))


class User(UserMixin):
    """A logged-in person: either a customer ("user") or an "admin".
    The Flask-Login id is stored as "user:<id>" or "admin:<id>"."""

    def __init__(self, kind, row_id, name, email="", phone=""):
        self.kind = kind
        self.id = f"{kind}:{row_id}"
        self.row_id = row_id
        self.name = name
        self.email = email
        self.phone = phone

    @property
    def is_admin(self):
        return self.kind == "admin"


def load_user_by_id(composite_id):
    kind, _, raw = str(composite_id).partition(":")
    if kind not in ("user", "admin") or not raw.isdigit():
        return None
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if kind == "admin":
                cur.execute("SELECT id, username FROM admins WHERE id=%s", (raw,))
                row = cur.fetchone()
                if row:
                    return User("admin", row["id"], row["username"])
            else:
                cur.execute("SELECT id, full_name, email, phone FROM users WHERE id=%s", (raw,))
                row = cur.fetchone()
                if row:
                    return User("user", row["id"], row["full_name"], row["email"], row["phone"])
    finally:
        conn.close()
    return None


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Please log in as admin to continue.", "info")
            return redirect(url_for("admin.login"))
        return view_func(*args, **kwargs)
    return wrapped


def safe_next(target, fallback):
    """Only allow redirects to local paths (blocks open-redirect tricks)."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return fallback


def rupee(amount):
    return "\u20b9{:,.2f}".format(float(amount))
