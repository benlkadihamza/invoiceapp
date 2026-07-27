import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_uNal2eUQkC4m@ep-winter-cloud-atpsnveg-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

from app import create_app
from models import db, Person, Transaction, Invoice, Product, PaymentMethod, User

app = create_app()

with app.app_context():
    print("=== TESTING ALL CREATE ENDPOINTS ON NEON POSTGRESQL ===")
    
    # 1. PERSONS CREATE
    p_count_before = Person.query.count()
    p = Person(name="AUDIT_PERSON_TEST", phone="0655443322", email="audit_person@test.com")
    db.session.add(p)
    db.session.commit()
    p_count_after = Person.query.count()
    print(f"[PERSONS] Add Executed: YES | Commit Executed: YES | ID: {p.id} | Count Before: {p_count_before} | Count After: {p_count_after}")

    # 2. PAYMENT METHODS CREATE
    pm_count_before = PaymentMethod.query.count()
    pm = PaymentMethod(name="AUDIT_PAYMENT_METHOD")
    db.session.add(pm)
    db.session.commit()
    pm_count_after = PaymentMethod.query.count()
    print(f"[PAYMENT METHODS] Add Executed: YES | Commit Executed: YES | ID: {pm.id} | Count Before: {pm_count_before} | Count After: {pm_count_after}")

    # 3. TRANSACTIONS CREATE
    t_count_before = Transaction.query.count()
    t = Transaction(description="AUDIT_TRANSACTION_TEST", income=250.0, expense=0.0, person_id=p.id, payment_method_id=pm.id)
    db.session.add(t)
    db.session.commit()
    t_count_after = Transaction.query.count()
    print(f"[TRANSACTIONS] Add Executed: YES | Commit Executed: YES | ID: {t.id} | Count Before: {t_count_before} | Count After: {t_count_after}")

    # 4. PRODUCTS CREATE
    prod_count_before = Product.query.count()
    prod = Product(title="AUDIT_PRODUCT_TEST", stock_quantity=15)
    db.session.add(prod)
    db.session.commit()
    prod_count_after = Product.query.count()
    print(f"[PRODUCTS] Add Executed: YES | Commit Executed: YES | ID: {prod.id} | Count Before: {prod_count_before} | Count After: {prod_count_after}")

    # 5. INVOICES CREATE
    inv_count_before = Invoice.query.count()
    inv = Invoice(invoice_num="AUDIT-INV-001", client_name="AUDIT_CLIENT_TEST", net_total=750.0)
    db.session.add(inv)
    db.session.commit()
    inv_count_after = Invoice.query.count()
    print(f"[INVOICES] Add Executed: YES | Commit Executed: YES | ID: {inv.id} | Count Before: {inv_count_before} | Count After: {inv_count_after}")

    print("\n=== VERIFYING IMMEDIATE ROW PERSISTENCE IN NEON ===")
    print("Person fetched:", Person.query.filter_by(name="AUDIT_PERSON_TEST").first().name)
    print("Transaction fetched:", Transaction.query.filter_by(description="AUDIT_TRANSACTION_TEST").first().description)
    print("Product fetched:", Product.query.filter_by(title="AUDIT_PRODUCT_TEST").first().title)
    print("Invoice fetched:", Invoice.query.filter_by(invoice_num="AUDIT-INV-001").first().invoice_num)
