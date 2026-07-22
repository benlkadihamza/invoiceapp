import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date


db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Person(db.Model):
    __tablename__ = 'persons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='person', lazy='dynamic')

    def transaction_count(self):
        return self.transactions.count()

    def total_income(self):
        return db.session.query(db.func.coalesce(db.func.sum(Transaction.income), 0.0)).filter(
            Transaction.person_id == self.id, Transaction.income > 0
        ).scalar() or 0.0

    def total_expense(self):
        return db.session.query(db.func.coalesce(db.func.sum(Transaction.expense), 0.0)).filter(
            Transaction.person_id == self.id, Transaction.expense > 0
        ).scalar() or 0.0

    def net_balance(self):
        return self.total_income() - self.total_expense()


class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    transactions = db.relationship('Transaction', backref='payment_method', lazy='dynamic')


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String(200), nullable=False)
    income = db.Column(db.Float, default=0.0)
    expense = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    receipt_image = db.Column(db.String(256))
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def net(self):
        return self.income - self.expense

    @property
    def formatted_date(self):
        return self.date.strftime('%d/%m/%Y') if self.date else ''


class Invoice(db.Model):
    __tablename__ = "invoices"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_num = db.Column(db.String, nullable=False, default="")
    date = db.Column(db.String, nullable=False, default="")
    client_name = db.Column(db.String, nullable=False, default="")
    client_address = db.Column(db.String, nullable=False, default="")
    total = db.Column(db.Float, nullable=False, default=0.0)
    remise = db.Column(db.Float, nullable=False, default=0.0)
    payer = db.Column(db.Float, nullable=False, default=0.0)
    net_total = db.Column(db.Float, nullable=False, default=0.0)
    items = db.Column(db.JSON, nullable=False, default=list)
    show_facture_num = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.String,
        default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False,
                     default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), unique=True, nullable=False)
    photo = db.Column(db.String(512), nullable=False, default="")
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.String,
        default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    updated_at = db.Column(
        db.String,
        default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        onupdate=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


class StockHistory(db.Model):
    __tablename__ = "stock_history"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    change_type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    stock_before = db.Column(db.Integer, nullable=False)
    stock_after = db.Column(db.Integer, nullable=False)
    created_at = db.Column(
        db.String,
        default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

