import os
import re
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from models import db, User
from config import config
from routes import register_blueprints


def _mask_url(url_str):
    if not url_str:
        return ""
    return re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', url_str)


def create_app(config_name=None):
    if config_name is None:
        if os.environ.get("FLASK_CONFIG"):
            config_name = os.environ.get("FLASK_CONFIG")
        elif os.environ.get("DATABASE_URL"):
            config_name = "production"
        else:
            config_name = "development"

    app = Flask(__name__)
    selected_config_cls = config.get(config_name, config['default'])
    app.config.from_object(selected_config_cls)

    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    masked_uri = _mask_url(uri)
    engine_name = 'postgresql' if uri.startswith('postgresql') else ('sqlite' if uri.startswith('sqlite') else 'unknown')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)

    db.init_app(app)
    csrf = CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_globals():
        from models import Person, PaymentMethod
        return {
            'all_persons': Person.query.order_by(Person.name).all(),
            'all_payment_methods': PaymentMethod.query.order_by(PaymentMethod.name).all(),
        }

    register_blueprints(app)

    with app.app_context():
        try:
            db.create_all()
            _seed_defaults()
        except Exception as e:
            print("=" * 60)
            print("DATABASE INITIALIZATION / SEEDING WARNING:", e)
            print("=" * 60)

        db_host = "None"
        db_name = "None"
        if uri.startswith('postgresql'):
            try:
                from sqlalchemy.engine import make_url
                parsed = make_url(uri)
                db_host = parsed.host or "None"
                db_name = parsed.database or "None"
            except Exception:
                db_host = str(db.engine.url.host)
                db_name = str(db.engine.url.database)
        elif uri.startswith('sqlite'):
            db_name = uri

        print("==================================================")
        print(f"ACTIVE CONFIG:\n{selected_config_cls.__name__}\n")
        print(f"DATABASE URL:\n{masked_uri}\n")
        print(f"DATABASE ENGINE:\n{engine_name}\n")
        print(f"HOST:\n{db_host}\n")
        print(f"DATABASE:\n{db_name}")
        print("==================================================")

        if os.environ.get('DATABASE_URL') and engine_name == 'sqlite':
            print("\n" + "=" * 50)
            print("ERROR:\nApplication is still running on SQLite.\n\nDATABASE_URL exists but ProductionConfig was not selected.")
            print("=" * 50 + "\n")

        from sqlalchemy import text
        try:
            current_db = db.session.execute(text("SELECT current_database()")).scalar()
            current_u = db.session.execute(text("SELECT current_user")).scalar()
            db_ver = db.session.execute(text("SELECT version()")).scalar()
            print("Current DB:", current_db)
            print("Current User:", current_u)
            print("Version:", db_ver)
        except Exception as e:
            print("Diagnostic Query Error:", e)

    @app.route("/debug/database-test")
    def debug_database_test():
        from models import Person
        from sqlalchemy import text
        import uuid

        test_name = f"DEBUG_PERSON_{uuid.uuid4().hex[:6]}"
        p = Person(name=test_name, phone="0000000000", email="debug@test.com")
        db.session.add(p)
        db.session.commit()

        inserted_p = Person.query.filter_by(name=test_name).first()

        current_db = "unknown"
        current_u = "unknown"
        try:
            current_db = db.session.execute(text("SELECT current_database()")).scalar()
            current_u = db.session.execute(text("SELECT current_user")).scalar()
        except Exception:
            pass

        eng = 'postgresql' if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('postgresql') else 'sqlite'

        return {
            "database": current_db,
            "user": current_u,
            "engine": eng,
            "inserted_id": inserted_p.id if inserted_p else None,
            "success": True
        }

    return app


def _seed_defaults():
    from models import PaymentMethod, User

    if PaymentMethod.query.count() == 0:
        methods = ['Espèces', 'Banque', 'Carte de crédit', 'Virement', 'Paiement mobile']
        for m in methods:
            db.session.add(PaymentMethod(name=m))

    if User.query.count() == 0:
        u = User(username='admin')
        u.set_password('admin123')
        db.session.add(u)

    db.session.commit()


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
