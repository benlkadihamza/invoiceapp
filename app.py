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
        db.create_all()
        _seed_defaults()

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

