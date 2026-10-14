import os
import uuid

from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, current_app)
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from db import get_connection
from helpers import admin_required, load_user_by_id

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_upload(file_storage):
    """Save an admin-uploaded product photo and return its stored filename."""
    if not file_storage or file_storage.filename == "":
        return None
    if not _allowed_file(file_storage.filename):
        flash("Image must be PNG, JPG or WEBP.", "error")
        return None
    ext = secure_filename(file_storage.filename).rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(current_app.root_path, "static", "uploads", "products")
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, filename))
    return filename


# ---------------------------------------------------------------- login ----
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM admins WHERE username=%s", (username,))
                row = cur.fetchone()
        finally:
            conn.close()

        if row and check_password_hash(row["password"], password):
            login_user(load_user_by_id(f"admin:{row['id']}"))
            return redirect(url_for("admin.dashboard"))

        flash("Invalid admin username or password.", "error")

    return render_template("admin/login.html")


@admin_bp.route("/register", methods=["GET", "POST"])
def register():
    """Create a new admin account. Needs the secret ADMIN_SIGNUP_CODE from .env."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        code = request.form.get("signup_code", "").strip()
        expected = os.environ.get("ADMIN_SIGNUP_CODE", "gudlar-admin-2026")

        errors = []
        if code != expected:
            errors.append("Invalid admin signup code.")
        if len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        new_id = None
        if not errors:
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM admins WHERE username=%s", (username,))
                    if cur.fetchone():
                        errors.append("That username is already taken.")
                    else:
                        cur.execute("INSERT INTO admins (username, password) VALUES (%s, %s)",
                                    (username, generate_password_hash(password)))
                        new_id = cur.lastrowid
            finally:
                conn.close()

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("admin/register.html", form=request.form)

        login_user(load_user_by_id(f"admin:{new_id}"))
        flash("Admin account created. Welcome!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/register.html", form={})


@admin_bp.route("/logout")
@admin_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


# ------------------------------------------------------------ dashboard ----
@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM products WHERE is_active=1")
            total_products = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM products WHERE is_active=1 AND stock > 0")
            in_stock = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM products WHERE is_active=1 AND stock = 0")
            out_of_stock = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM users")
            total_customers = cur.fetchone()["n"]

            cur.execute("""
                SELECT p.*, c.name AS category_name FROM products p
                JOIN categories c ON c.id = p.category_id
                WHERE p.is_active = 1
                ORDER BY p.created_at DESC LIMIT 6
            """)
            recent_products = cur.fetchall()
    finally:
        conn.close()

    return render_template(
        "admin/dashboard.html",
        total_products=total_products,
        in_stock=in_stock,
        out_of_stock=out_of_stock,
        total_customers=total_customers,
        recent_products=recent_products,
    )


# ------------------------------------------------------------- products ----
@admin_bp.route("/products")
@admin_required
def products():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.*, c.name AS category_name FROM products p
                JOIN categories c ON c.id = p.category_id
                ORDER BY p.id DESC
            """)
            items = cur.fetchall()
    finally:
        conn.close()
    return render_template("admin/products.html", items=items)


@admin_bp.route("/products/add", methods=["GET", "POST"])
@admin_required
def add_product():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM categories ORDER BY name")
            categories = cur.fetchall()

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            category_id = request.form.get("category_id")
            description = request.form.get("description", "").strip()
            price = request.form.get("price", "").strip()
            size_label = request.form.get("size_label", "").strip() or "1 Litre"
            stock = request.form.get("stock", "0").strip()

            errors = []
            if not name:
                errors.append("Product name is required.")
            if not category_id:
                errors.append("Please choose a category.")
            try:
                price = float(price)
                if price <= 0:
                    errors.append("Price must be greater than 0.")
            except ValueError:
                errors.append("Price must be a valid number.")
            try:
                stock = int(stock)
                if stock < 0:
                    errors.append("Stock cannot be negative.")
            except ValueError:
                errors.append("Stock must be a whole number.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template(
                    "admin/add_product.html", categories=categories, form=request.form
                )

            image_filename = _save_upload(request.files.get("image"))

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO products
                        (category_id, name, description, price, size_label, image, stock, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                """, (category_id, name, description, price, size_label, image_filename, stock))

            flash("New product launched and added to the site.", "success")
            return redirect(url_for("admin.products"))
    finally:
        conn.close()

    return render_template("admin/add_product.html", categories=categories, form={})


@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM categories ORDER BY name")
            categories = cur.fetchall()
            cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
            product = cur.fetchone()

        if not product:
            flash("Product not found.", "error")
            return redirect(url_for("admin.products"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            category_id = request.form.get("category_id")
            description = request.form.get("description", "").strip()
            price = request.form.get("price", "").strip()
            size_label = request.form.get("size_label", "").strip() or "1 Litre"
            stock = request.form.get("stock", "0").strip()
            is_active = 1 if request.form.get("is_active") == "on" else 0

            errors = []
            if not name:
                errors.append("Product name is required.")
            try:
                price = float(price)
                if price <= 0:
                    errors.append("Price must be greater than 0.")
            except ValueError:
                errors.append("Price must be a valid number.")
            try:
                stock = int(stock)
                if stock < 0:
                    errors.append("Stock cannot be negative.")
            except ValueError:
                errors.append("Stock must be a whole number.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template(
                    "admin/edit_product.html", product=product, categories=categories
                )

            new_image = _save_upload(request.files.get("image"))
            image_filename = new_image or product["image"]

            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE products SET
                        category_id=%s, name=%s, description=%s, price=%s,
                        size_label=%s, image=%s, stock=%s, is_active=%s
                    WHERE id=%s
                """, (category_id, name, description, price, size_label,
                      image_filename, stock, is_active, product_id))

            flash("Product updated.", "success")
            return redirect(url_for("admin.products"))
    finally:
        conn.close()

    return render_template("admin/edit_product.html", product=product, categories=categories)


@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def delete_product(product_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE products SET is_active=0 WHERE id=%s", (product_id,))
    finally:
        conn.close()
    flash("Product removed from the shop.", "info")
    return redirect(url_for("admin.products"))
