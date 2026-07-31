import unittest
import threading
import uuid
from app import create_app
from models import db, Person, Transaction, Product, PaymentMethod, Invoice, User

class TestIdempotencyAndDuplicatePrevention(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('development')
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
        with cls.app.app_context():
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
            cls.admin_id = admin.id

    def _get_client(self):
        c = self.app.test_client()
        with c.session_transaction() as sess:
            sess['_user_id'] = str(self.admin_id)
            sess['_fresh'] = True
        return c

    def test_01_rapid_person_creation(self):
        """Test submitting Person form 20 times rapidly with same token -> only 1 record created"""
        with self.app.app_context():
            initial_count = Person.query.count()
            test_token = f"test_person_token_{uuid.uuid4().hex}"
            unique_name = f"Test_Person_{uuid.uuid4().hex[:6]}"

            responses = []
            def send_post():
                with self.app.app_context():
                    c = self._get_client()
                    resp = c.post('/persons/add', data={
                        'name': unique_name,
                        'phone': '0612345678',
                        'email': 'test@example.com',
                        'notes': 'Test notes',
                        'request_token': test_token
                    })
                    responses.append(resp.status_code)

            threads = []
            for _ in range(20):
                t = threading.Thread(target=send_post)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            final_count = Person.query.count()
            created_persons = Person.query.filter_by(name=unique_name).all()
            print(f"\n[TEST 1 - PERSONS] Rapid 20x POST requests with same token:")
            print(f"  HTTP Responses: {responses[:5]}...")
            print(f"  Created rows: {len(created_persons)}")
            print(f"  Total Persons before: {initial_count}, after: {final_count}")
            self.assertEqual(len(created_persons), 1, "Expected exactly 1 person record inserted!")
            self.assertEqual(final_count, initial_count + 1)

    def test_02_rapid_payment_method_creation(self):
        """Test submitting Payment Method form 20 times rapidly -> only 1 record created"""
        with self.app.app_context():
            initial_count = PaymentMethod.query.count()
            test_token = f"test_pm_token_{uuid.uuid4().hex}"
            unique_pm = f"PM_{uuid.uuid4().hex[:6]}"

            responses = []
            def send_post():
                with self.app.app_context():
                    c = self._get_client()
                    resp = c.post('/payment-methods/add', data={
                        'name': unique_pm,
                        'request_token': test_token
                    })
                    responses.append(resp.status_code)

            threads = []
            for _ in range(20):
                t = threading.Thread(target=send_post)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            final_count = PaymentMethod.query.count()
            created_pms = PaymentMethod.query.filter_by(name=unique_pm).all()
            print(f"\n[TEST 2 - PAYMENT METHODS] Rapid 20x POST requests with same token:")
            print(f"  HTTP Responses: {responses[:5]}...")
            print(f"  Created rows: {len(created_pms)}")
            print(f"  Total PaymentMethods before: {initial_count}, after: {final_count}")
            self.assertEqual(len(created_pms), 1, "Expected exactly 1 payment method inserted!")
            self.assertEqual(final_count, initial_count + 1)

    def test_03_rapid_transaction_creation(self):
        """Test submitting Transaction form 20 times rapidly -> only 1 record created"""
        with self.app.app_context():
            person = Person.query.first()
            if not person:
                person = Person(name="TestPerson")
                db.session.add(person)
                db.session.commit()

            initial_count = Transaction.query.count()
            test_token = f"test_txn_token_{uuid.uuid4().hex}"
            unique_desc = f"Txn_{uuid.uuid4().hex[:6]}"

            responses = []
            def send_post():
                with self.app.app_context():
                    c = self._get_client()
                    resp = c.post('/transactions/add', data={
                        'date': '2026-07-31',
                        'person_id': person.id,
                        'description': unique_desc,
                        'income': '150.00',
                        'expense': '0.00',
                        'request_token': test_token
                    })
                    responses.append(resp.status_code)

            threads = []
            for _ in range(20):
                t = threading.Thread(target=send_post)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            final_count = Transaction.query.count()
            created_txns = Transaction.query.filter_by(description=unique_desc).all()
            print(f"\n[TEST 3 - TRANSACTIONS] Rapid 20x POST requests with same token:")
            print(f"  HTTP Responses: {responses[:5]}...")
            print(f"  Created rows: {len(created_txns)}")
            print(f"  Total Transactions before: {initial_count}, after: {final_count}")
            self.assertEqual(len(created_txns), 1, "Expected exactly 1 transaction inserted!")
            self.assertEqual(final_count, initial_count + 1)

    def test_04_rapid_product_creation(self):
        """Test submitting Product creation 20 times rapidly -> only 1 record created"""
        with self.app.app_context():
            initial_count = Product.query.count()
            test_token = f"test_prod_token_{uuid.uuid4().hex}"
            unique_prod = f"Product_{uuid.uuid4().hex[:6]}"

            responses = []
            def send_post():
                with self.app.app_context():
                    c = self._get_client()
                    resp = c.post('/stock/add', data={
                        'title': unique_prod,
                        'request_token': test_token
                    })
                    responses.append(resp.status_code)

            threads = []
            for _ in range(20):
                t = threading.Thread(target=send_post)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            final_count = Product.query.count()
            created_prods = Product.query.filter_by(title=unique_prod).all()
            print(f"\n[TEST 4 - PRODUCTS] Rapid 20x POST requests with same token:")
            print(f"  HTTP Responses: {responses[:5]}...")
            print(f"  Created rows: {len(created_prods)}")
            print(f"  Total Products before: {initial_count}, after: {final_count}")
            self.assertEqual(len(created_prods), 1, "Expected exactly 1 product inserted!")
            self.assertEqual(final_count, initial_count + 1)

    def test_05_rapid_invoice_creation(self):
        """Test submitting Invoice creation 20 times rapidly -> only 1 record created"""
        with self.app.app_context():
            initial_count = Invoice.query.count()
            test_token = f"test_inv_token_{uuid.uuid4().hex}"
            unique_num = f"INV_{uuid.uuid4().hex[:6]}"

            responses = []
            def send_post():
                with self.app.app_context():
                    c = self._get_client()
                    resp = c.post('/invoices/save', json={
                        'invoice_num': unique_num,
                        'date': '2026-07-31',
                        'client_name': 'Test Client',
                        'client_address': 'Test Address',
                        'items': [{'description': 'Item 1', 'quantity': 2, 'unit_price': 100, 'total': 200}],
                        'total': 200,
                        'net_total': 200,
                        'request_token': test_token
                    })
                    responses.append(resp.status_code)

            threads = []
            for _ in range(20):
                t = threading.Thread(target=send_post)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            final_count = Invoice.query.count()
            created_invoices = Invoice.query.filter_by(invoice_num=unique_num).all()
            print(f"\n[TEST 5 - INVOICES] Rapid 20x POST requests with same token:")
            print(f"  HTTP Responses: {responses[:5]}...")
            print(f"  Created rows: {len(created_invoices)}")
            print(f"  Total Invoices before: {initial_count}, after: {final_count}")
            self.assertEqual(len(created_invoices), 1, "Expected exactly 1 invoice inserted!")
            self.assertEqual(final_count, initial_count + 1)

if __name__ == '__main__':
    unittest.main()
