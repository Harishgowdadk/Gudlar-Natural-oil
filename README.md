# Gudlar — Sri Renuka Oil's

A product-catalog website for Gudlar's Sri Renuka Oil's (coconut oil &amp;
groundnut oil). Visitors browse products, see live stock status, add
items to a cart, enter name / 10-digit phone / address, and tap
**Order on WhatsApp** — the order opens in WhatsApp with all items
pre-filled, addressed to your number. There is **no online payment**.
The admin adds and manages products (with photos) and stock.

Backend: **Python (Flask)**
Database: **MySQL**, run through **XAMPP** (Apache isn't needed — only
XAMPP's MySQL service and, optionally, phpMyAdmin to import the schema).

---

## 1. Start MySQL in XAMPP

1. Open the **XAMPP Control Panel**.
2. Click **Start** next to **MySQL**. (You don't need to start Apache —
   Flask runs its own server.)

## 2. Create the database

1. Open **phpMyAdmin** (`http://localhost/phpmyadmin`).
2. Click **Import**, choose the file `sql/gudlar.sql` from this project,
   and click **Go**.
   - This creates the `gudlar_db` database with `admins`, `categories`
     and `products` tables, plus 6 sample products.

## 3. Install Python & the project dependencies

Make sure you have **Python 3.10+** installed, then from the project
folder:

```bash
# (optional but recommended) create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

## 4. Configure environment variables

Copy `.env.example` to `.env` in the same folder:

```bash
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux
```

The defaults already match a fresh XAMPP install (`root` user, no
password, `localhost:3306`). Only change `.env` if your MySQL setup is
different.

## 4b. Set your WhatsApp number

In `.env`, set `WHATSAPP_NUMBER` to your number with country code,
digits only (India example: `919876543210`). Orders go to this number.

## 4c. Accounts (customers and admins)

- **Customers** register at `/register` (name, email, 10-digit phone,
  password) and log in at `/login`. Browsing and the cart work without
  an account, but a customer must be logged in to send an order on
  WhatsApp. Their name and phone are pre-filled in the cart.
- **Admins** log in at `/admin/login`. New admin accounts are created at
  `/admin/register` and need the secret code `ADMIN_SIGNUP_CODE` from
  your `.env` file. **Change that code**, and don't share it publicly.
- Passwords are stored hashed, never as plain text.

## 5. Run the website

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser. The public catalog
needs no login.

## 6. Admin panel

Go to **http://127.0.0.1:5000/admin/login**.

- **Username:** `admin`
- **Password:** `admin123`

<!-- user
Hari
hari@gmail.com
Hari@123 -->

This account is created automatically the first time the app starts
(see `db.py` → `ensure_default_admin()`), so there's no manual setup
step. **Change this password before going live** (you'll need to add a
"change password" screen, or update it directly in the `admins` table
via phpMyAdmin using a bcrypt hash from `werkzeug.security.generate_password_hash`).

From the admin dashboard you can:
- See how many products are in stock / out of stock.
- **Add a new product** — name, category, size, price, stock count, a
  description, and **upload a custom photo** for it. Leave the photo
  empty to use a default placeholder bottle image.
- Edit any product's details, photo, or stock count.
- Remove a product from the site (soft-delete — it's hidden, not
  deleted from the database).

Stock status on the website is automatic: it's calculated from the
**Stock Quantity** you set.
- `0` → "Out of Stock"
- `1–10` → "Only X left" (low stock)
- `11+` → "In Stock"

---

## Project structure

```
gudlar_flask/
├── app.py                  # Main entry point — run this to start the site
├── db.py                   # MySQL connection + auto-creates default admin
├── helpers.py               # Shared helpers (admin auth, currency formatting)
├── shop.py                  # Public routes: home, product list, product detail
├── admin.py                  # Admin routes: login, dashboard, add/edit/remove products
├── requirements.txt
├── .env.example              # Copy to .env
├── sql/
│   └── gudlar.sql             # Import this in phpMyAdmin first
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   ├── images/                # Favicon, placeholder bottle, brand seal
│   └── uploads/products/      # Admin-uploaded product photos land here
└── templates/
    ├── base.html               # Header + footer, used by every public page
    ├── index.html               # Homepage
    ├── products.html             # Product listing with category filters
    ├── product_detail.html        # Single product page
    ├── _product_card.html          # Reusable product card (used on 2 pages)
    └── admin/
        ├── base_admin.html          # Admin layout with sidebar
        ├── login.html
        ├── dashboard.html
        ├── products.html
        ├── add_product.html
        └── edit_product.html
```

## Notes

- Uploaded product photos are stored in `static/uploads/products/` with
  randomly generated filenames, so two products can safely use
  differently named source files without colliding.
- Allowed photo formats: PNG, JPG, JPEG, WEBP (max 5 MB).
- The cart is stored in the visitor's browser session (no customer login).
  Quantities are limited to the stock you set; out-of-stock items cannot
  be added.
- Phone numbers must be exactly 10 digits starting with 6-9 (enforced in
  the browser and again on the server).
- This is Flask's built-in development server, fine for local use/testing.
  For a real public launch, run it behind a production server (e.g.
  `waitress` on Windows, or `gunicorn` on Linux/macOS) rather than
  `python app.py`.
