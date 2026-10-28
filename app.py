import os
from datetime import date

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

from db import ensure_default_admin, ensure_users_table
from helpers import load_user_by_id, rupee
from shop import shop_bp, whatsapp_number
from admin import admin_bp
from auth import auth_bp

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(composite_id):
    return load_user_by_id(composite_id)


app.register_blueprint(shop_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)


@app.context_processor
def inject_globals():
    from flask import session
    wa = whatsapp_number()
    return {
        "rupee": rupee,
        "current_year": date.today().year,
        "cart_count": sum(int(q) for q in session.get("cart", {}).values()),
        "wa_number": wa,
        "wa_display": ("+" + wa[:2] + " " + wa[2:7] + " " + wa[7:]) if len(wa) == 12 else ("+" + wa),
    }

with app.app_context():
    try:
        ensure_users_table()
        ensure_default_admin()
    except Exception as exc:  # pragma: no cover
        print("Could not create default admin (is MySQL running in XAMPP?):", exc)

if __name__ == "__main__":
    app.run(debug=True, port=5000)