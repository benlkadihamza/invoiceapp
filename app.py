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
        if os.environ.get('FLASK_CONFIG'):
            config_name = os.environ.get('FLASK_CONFIG')
        elif os.environ.get('FLASK_ENV'):
            config_name = os.environ.get('FLASK_ENV')
        elif os.environ.get('DATABASE_URL'):
            config_name = 'production'
        else:
            config_name = 'default'

    app = Flask(__name__)
    selected_config_cls = config.get(config_name, config['default'])
    app.config.from_object(selected_config_cls)

    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    masked_uri = _mask_url(uri)
    engine_name = 'postgresql' if uri.startswith('postgresql') else ('sqlite' if uri.startswith('sqlite') else 'unknown')

    print("==================================================")
    print(f"ACTIVE CONFIG:\n{selected_config_cls.__name__}")
    print(f"DATABASE URL:\n{masked_uri}")
    print(f"DATABASE ENGINE:\n{engine_name}")
    print("==================================================")

    if os.environ.get('DATABASE_URL') and engine_name == 'sqlite':
        print("WARNING: DATABASE_URL is set in environment, but SQLite was selected!")

    if (os.environ.get('RENDER') or os.environ.get('RENDER_SERVICE_ID')) and engine_name == 'sqlite':
        print("!" * 60)
        print("CRITICAL ALERT: DEPLOYED ON RENDER BUT DATABASE_URL IS MISSING!")
        print("Your service is running on local SQLite (ephemeral disk).")
        print("Data WILL BE ERASED every time Render restarts or reloads!")
        print("Fix: Go to Render Dashboard -> Environment Variables")
        print("Add Key: DATABASE_URL")
        print("Add Value: postgresql://neondb_owner:npg_uNal2eUQkC4m@ep-winter-cloud-atpsnveg-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
        print("!" * 60)


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

        print("=" * 60)
        print("SQLALCHEMY_DATABASE_URI:", masked_uri)
        print("Engine:", db.engine.url)
        print("Host:", db.engine.url.host)
        print("Database:", db.engine.url.database)
        print("User:", db.engine.url.username)
        print("=" * 60)

        from sqlalchemy import text
        try:
            print("Current DB:", db.session.execute(text("SELECT current_database()")).scalar())
            print("Current User:", db.session.execute(text("SELECT current_user")).scalar())
            print("Version:", db.session.execute(text("SELECT version()")).scalar())
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
        current_db = db.session.execute(text("SELECT current_database()")).scalar()
        current_u = db.session.execute(text("SELECT current_user")).scalar()

        return {
            "success": True,
            "inserted_id": inserted_p.id if inserted_p else None,
            "inserted_name": inserted_p.name if inserted_p else None,
            "current_database": current_db,
            "current_user": current_u,
            "engine_url": _mask_url(str(db.engine.url)),
            "host": db.engine.url.host,
            "database": db.engine.url.database,
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

