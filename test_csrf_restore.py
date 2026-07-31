import unittest
import io
import re
import sqlite3
import os
from app import create_app
from models import db, User

def create_valid_sqlite_bytes():
    temp_path = "temp_dummy.db"
    conn = sqlite3.connect(temp_path)
    conn.execute("CREATE TABLE dummy (id INT)")
    conn.commit()
    conn.close()
    with open(temp_path, "rb") as f:
        data = f.read()
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return data

class TestCSRFDatabaseRestore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('development')
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = True  # STRICT CSRF ENABLED

        with cls.app.app_context():
            db.create_all()
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
            cls.admin_id = admin.id

    def setUp(self):
        self.client = self.app.test_client()
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin_id)
            sess['_fresh'] = True

    def test_01_settings_page_loads_and_contains_csrf_token(self):
        """Verify Settings page renders and contains csrf_token in HTML"""
        response = self.client.get('/settings/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        print("\n[CSRF TEST 1] Settings page render:")
        print(f"  Status code: {response.status_code}")
        print(f"  Contains csrf_token input field: {'name=\"csrf_token\"' in html}")

        self.assertIn('name="csrf_token"', html)

    def test_02_restore_form_submission_with_valid_csrf_token(self):
        """Verify database restore form submits cleanly when valid CSRF token is provided"""
        res = self.client.get('/settings/', follow_redirects=True)
        html = res.get_data(as_text=True)

        match = re.search(r'name="csrf_token"\s+type="hidden"\s+value="([^"]+)"', html)
        if not match:
            match = re.search(r'value="([^"]+)"\s+id="csrf_token"', html)
        if not match:
            match = re.search(r'input[^>]+name="csrf_token"[^>]+value="([^"]+)"', html)
        self.assertIsNotNone(match, "Could not extract csrf_token from settings page HTML!")
        csrf_token = match.group(1)

        db_bytes = create_valid_sqlite_bytes()
        valid_db = (io.BytesIO(db_bytes), 'test_restore.db')

        post_res = self.client.post('/settings/backup/restore', data={
            'csrf_token': csrf_token,
            'request_token': 'test_req_token_123',
            'database_file': valid_db
        }, content_type='multipart/form-data')

        print("\n[CSRF TEST 2] Submit Restore form WITH CSRF Token:")
        print(f"  Response status: {post_res.status_code}")
        print(f"  Redirect target: {post_res.headers.get('Location')}")

        self.assertEqual(post_res.status_code, 302)
        self.assertIn('/settings', post_res.headers.get('Location'))

        # Re-initialize tables so remaining tests run on clean db
        with self.app.app_context():
            db.create_all()
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()

    def test_03_restore_form_submission_without_csrf_token_fails(self):
        """Verify that submitting WITHOUT a CSRF token returns 400 Bad Request (CSRF protection active!)"""
        db_bytes = create_valid_sqlite_bytes()
        valid_db = (io.BytesIO(db_bytes), 'test_restore.db')

        post_res = self.client.post('/settings/backup/restore', data={
            'request_token': 'test_req_token_456',
            'database_file': valid_db
        }, content_type='multipart/form-data')

        print("\n[CSRF TEST 3] Submit Restore form WITHOUT CSRF Token:")
        print(f"  Response status: {post_res.status_code}")
        print(f"  Is 400 Bad Request: {post_res.status_code == 400}")

        self.assertEqual(post_res.status_code, 400)
        self.assertIn("The CSRF token is missing", post_res.get_data(as_text=True))

    def test_04_backup_download_still_works(self):
        """Verify backup download still works cleanly"""
        res = self.client.get('/settings/backup/download')
        self.assertEqual(res.status_code, 200)
        self.assertIn('.db', res.headers.get('Content-Disposition', ''))
        print("\n[CSRF TEST 4] Backup download: PASS")

if __name__ == '__main__':
    unittest.main()
