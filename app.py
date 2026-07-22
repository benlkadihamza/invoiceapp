import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from models import db, User
from config import config
from routes import register_blueprints


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

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
        _clean_database()
        _seed_defaults()

    return app


def _clean_database():
    from models import Transaction
    import sqlalchemy as sa

    inspector = sa.inspect(db.engine)
    table_names = inspector.get_table_names()

    if 'categories' in table_names:
        db.session.execute(sa.text('DROP TABLE categories'))
        db.session.commit()

    if 'transactions' in table_names:
        columns = [col['name'] for col in inspector.get_columns('transactions')]
        if 'transaction_type' in columns:
            db.session.execute(sa.text(
                "CREATE TABLE IF NOT EXISTS transactions_backup AS "
                "SELECT id, date, description, income, expense, notes, receipt_image, "
                "person_id, payment_method_id, created_at FROM transactions"
            ))
            db.session.execute(sa.text('DROP TABLE transactions'))
            db.session.execute(sa.text(
                "CREATE TABLE transactions ("
                "id INTEGER PRIMARY KEY, "
                "date DATE NOT NULL, "
                "description VARCHAR(200) NOT NULL, "
                "income FLOAT DEFAULT 0.0, "
                "expense FLOAT DEFAULT 0.0, "
                "notes TEXT, "
                "receipt_image VARCHAR(256), "
                "person_id INTEGER NOT NULL REFERENCES persons(id), "
                "payment_method_id INTEGER REFERENCES payment_methods(id), "
                "created_at DATETIME)"
            ))
            db.session.execute(sa.text(
                "INSERT INTO transactions (id, date, description, income, expense, notes, "
                "receipt_image, person_id, payment_method_id, created_at) "
                "SELECT id, date, description, income, expense, notes, "
                "receipt_image, person_id, payment_method_id, created_at "
                "FROM transactions_backup"
            ))
            db.session.execute(sa.text('DROP TABLE transactions_backup'))
            db.session.commit()
        elif 'category_id' in columns:
            db.session.execute(sa.text(
                "CREATE TABLE IF NOT EXISTS transactions_backup AS "
                "SELECT id, date, description, income, expense, notes, receipt_image, "
                "person_id, payment_method_id, created_at FROM transactions"
            ))
            db.session.execute(sa.text('DROP TABLE transactions'))
            db.session.execute(sa.text(
                "CREATE TABLE transactions ("
                "id INTEGER PRIMARY KEY, "
                "date DATE NOT NULL, "
                "description VARCHAR(200) NOT NULL, "
                "income FLOAT DEFAULT 0.0, "
                "expense FLOAT DEFAULT 0.0, "
                "notes TEXT, "
                "receipt_image VARCHAR(256), "
                "person_id INTEGER NOT NULL REFERENCES persons(id), "
                "payment_method_id INTEGER REFERENCES payment_methods(id), "
                "created_at DATETIME)"
            ))
            db.session.execute(sa.text(
                "INSERT INTO transactions (id, date, description, income, expense, notes, "
                "receipt_image, person_id, payment_method_id, created_at) "
                "SELECT id, date, description, income, expense, notes, "
                "receipt_image, person_id, payment_method_id, created_at "
                "FROM transactions_backup"
            ))
            db.session.execute(sa.text('DROP TABLE transactions_backup'))
            db.session.commit()


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
