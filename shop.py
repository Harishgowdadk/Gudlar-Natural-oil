import os
import re
import urllib.parse

from flask import (Blueprint, render_template, request, redirect, url_for,
                    session, flash)

from flask_login import current_user

from db import get_connection

PHONE_RE = re.compile(r"^[6-9][0-9]{9}$")

shop_bp = Blueprint("shop", __name__)


@shop_bp.route("/")
def index():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.*, c.name AS category_name, c.slug AS category_slug
                FROM products p JOIN categories c ON c.id = p.category_id
                WHERE p.is_active = 1
                ORDER BY p.id ASC LIMIT 6
            """)
            featured = cur.fetchall()
    finally:
        conn.close()
    return render_template("index.html", featured=featured)


@shop_bp.route("/products")
def products():
    category_slug = request.args.get("category", "")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if category_slug:
                cur.execute("""
                    SELECT p.*, c.name AS category_name, c.slug AS category_slug
                    FROM products p JOIN categories c ON c.id = p.category_id
                    WHERE p.is_active = 1 AND c.slug = %s
                    ORDER BY p.id ASC
                """, (category_slug,))
            else:
                cur.execute("""
                    SELECT p.*, c.name AS category_name, c.slug AS category_slug
                    FROM products p JOIN categories c ON c.id = p.category_id
                    WHERE p.is_active = 1
                    ORDER BY p.id ASC
                """)
            items = cur.fetchall()
            cur.execute("SELECT * FROM categories ORDER BY name")
            categories = cur.fetchall()
    finally:
        conn.close()
    return render_template(
        "products.html", items=items, categories=categories, active_slug=category_slug
    )


@shop_bp.route("/products/<int:product_id>")
def product_detail(product_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.*, c.name AS category_name, c.slug AS category_slug
                FROM products p JOIN categories c ON c.id = p.category_id
                WHERE p.id = %s AND p.is_active = 1
            """, (product_id,))
            product = cur.fetchone()
            if not product:
                return redirect(url_for("shop.products"))

            cur.execute("""
                SELECT * FROM products
                WHERE category_id = %s AND id != %s AND is_active = 1
                LIMIT 4
            """, (product["category_id"], product_id))
            related = cur.fetchall()
    finally:
        conn.close()
    return render_template("product_detail.html", product=product, related=related)


# ====================================================================
# CART (kept in the visitor's session - no login, no payment)
# ====================================================================
def whatsapp_number():
    """Digits only, with country code, e.g. 919876543210"""
    return re.sub(r"\D", "", os.environ.get("WHATSAPP_NUMBER", "917090396819"))


def _load_cart_items():
    """Return (items, total). Quantities are clamped to current stock."""
    cart = session.get("cart", {})
    if not cart:
        return [], 0.0
    ids = [int(i) for i in cart.keys()]
    placeholders = ",".join(["%s"] * len(ids))
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT p.*, c.name AS category_name
                FROM products p JOIN categories c ON c.id = p.category_id
                WHERE p.is_active = 1 AND p.id IN ({placeholders})
            """, ids)
            rows = cur.fetchall()
    finally:
        conn.close()

    items, total, new_cart = [], 0.0, {}
    for p in rows:
        if p["stock"] <= 0:
            continue
        qty = min(int(cart.get(str(p["id"]), 1)), p["stock"])
        p["qty"] = qty
        p["line_total"] = float(p["price"]) * qty
        total += p["line_total"]
        items.append(p)
        new_cart[str(p["id"])] = qty
    if new_cart != cart:
        session["cart"] = new_cart
    return items, total


@shop_bp.route("/cart")
def cart():
    items, total = _load_cart_items()
    return render_template("cart.html", items=items, total=total, form={})


@shop_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    try:
        qty = max(1, int(request.form.get("quantity", 1)))
    except ValueError:
        qty = 1
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id=%s AND is_active=1", (product_id,))
            p = cur.fetchone()
    finally:
        conn.close()
    if not p or p["stock"] <= 0:
        flash("Sorry, that product is out of stock right now.", "error")
        return redirect(request.referrer or url_for("shop.products"))

    cart = session.get("cart", {})
    new_qty = min(int(cart.get(str(product_id), 0)) + qty, p["stock"])
    cart[str(product_id)] = new_qty
    session["cart"] = cart
    flash(f"Added to your cart: {p['name']} ({p['size_label']}).", "success")
    return redirect(url_for("shop.cart"))


@shop_bp.route("/cart/update/<int:product_id>", methods=["POST"])
def cart_update(product_id):
    try:
        qty = int(request.form.get("quantity", 1))
    except ValueError:
        qty = 1
    cart = session.get("cart", {})
    if str(product_id) in cart:
        if qty <= 0:
            cart.pop(str(product_id))
        else:
            cart[str(product_id)] = qty
        session["cart"] = cart
    return redirect(url_for("shop.cart"))


@shop_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
def cart_remove(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    flash("Item removed from your cart.", "info")
    return redirect(url_for("shop.cart"))


@shop_bp.route("/cart/order", methods=["POST"])
def place_order():
    """Validate details, build the order message and open WhatsApp."""
    if not current_user.is_authenticated or current_user.is_admin:
        flash("Please log in or register to place your order.", "info")
        return redirect(url_for("auth.login", next=url_for("shop.cart")))
    items, total = _load_cart_items()
    if not items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("shop.products"))

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    note = request.form.get("note", "").strip()

    errors = []
    if not name:
        errors.append("Please enter your name.")
    if not PHONE_RE.match(phone):
        errors.append("Phone number must be exactly 10 digits (starting with 6-9).")
    if not address:
        errors.append("Please enter your delivery address.")
    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("cart.html", items=items, total=total, form=request.form)

    lines = ["Hello Gudlar! I would like to order:", ""]
    for n, p in enumerate(items, 1):
        lines.append(f"{n}. {p['name']} ({p['size_label']}) x {p['qty']} = Rs.{p['line_total']:.2f}")
    lines += [
        "",
        f"Total: Rs.{total:.2f}",
        "",
        f"Name: {name}",
        f"Phone: {phone}",
        f"Address: {address}",
    ]
    if note:
        lines.append(f"Note: {note}")
    lines += ["", "Please confirm availability and delivery. Thank you!"]

    url = f"https://wa.me/{whatsapp_number()}?text={urllib.parse.quote(chr(10).join(lines))}"
    session.pop("cart", None)
    return redirect(url)
