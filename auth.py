from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_connection
from helpers import valid_phone, load_user_by_id, safe_next

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated and not current_user.is_admin:
        return redirect(url_for("shop.index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not full_name:
            errors.append("Please enter your full name.")
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")
        if not valid_phone(phone):
            errors.append("Phone number must be exactly 10 digits (starting with 6-9).")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        new_id = None
        if not errors:
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
                    if cur.fetchone():
                        errors.append("An account with this email already exists. Please log in.")
                    else:
                        cur.execute(
                            "INSERT INTO users (full_name, email, phone, password) VALUES (%s,%s,%s,%s)",
                            (full_name, email, phone, generate_password_hash(password)),
                        )
                        new_id = cur.lastrowid
            finally:
                conn.close()

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html", form=request.form)

        login_user(load_user_by_id(f"user:{new_id}"))
        flash("Welcome to Gudlar! Your account has been created.", "success")
        return redirect(safe_next(request.args.get("next"), url_for("shop.index")))

    return render_template("register.html", form={})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and not current_user.is_admin:
        return redirect(url_for("shop.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, password FROM users WHERE email=%s", (email,))
                row = cur.fetchone()
        finally:
            conn.close()

        if row and check_password_hash(row["password"], password):
            login_user(load_user_by_id(f"user:{row['id']}"))
            flash("Logged in successfully.", "success")
            return redirect(safe_next(request.args.get("next"), url_for("shop.index")))
        flash("Invalid email or password.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("shop.index"))
