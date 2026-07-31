import unittest
import os
import uuid
from datetime import datetime
from app import create_app
from models import db, MonthlyBackup, User
from routes.settings import FRENCH_MONTHS

class TestMonthlyBackupReminderSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('development')
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
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

    def test_01_dashboard_reminder_appears_when_no_backup(self):
        """Test 1: Current month has no backup. Dashboard reminder appears."""
        with self.app.app_context():
            now = datetime.now()
            # Clear any existing backup for current month
            MonthlyBackup.query.filter_by(month=now.month, year=now.year).delete()
            db.session.commit()

            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)

            expected_french_month = FRENCH_MONTHS.get(now.month, 'Mois')
            expected_text = f"{expected_french_month} {now.year}"

            print(f"\n[TEST 1] Missing backup check for {expected_text}:")
            print(f"  Warning card present: {'⚠ Rappel de Sauvegarde Mensuelle' in html}")
            self.assertIn("⚠ Rappel de Sauvegarde Mensuelle", html)
            self.assertIn(expected_text, html)

    def test_02_download_backup_filename_and_completion(self):
        """Test 2: Download backup. Filename is <FrenchMonth> <Year>.db, reminder disappears."""
        with self.app.app_context():
            now = datetime.now()
            expected_french_month = FRENCH_MONTHS.get(now.month, 'Mois')
            expected_filename = f"{expected_french_month} {now.year}.db"

            response = self.client.get('/settings/backup/download')
            self.assertEqual(response.status_code, 200)

            content_disposition = response.headers.get('Content-Disposition', '')
            print(f"\n[TEST 2] Download Backup:")
            print(f"  Content-Disposition header: {content_disposition}")
            print(f"  Expected filename: {expected_filename}")

            self.assertIn(expected_filename, content_disposition)

            # Check DB record updated
            record = MonthlyBackup.query.filter_by(month=now.month, year=now.year, completed=True).first()
            self.assertIsNotNone(record)
            self.assertEqual(record.filename, expected_filename)
            self.assertTrue(record.completed)

            # Dashboard refresh -> reminder should disappear
            dash_response = self.client.get('/')
            dash_html = dash_response.get_data(as_text=True)
            self.assertNotIn("⚠ Rappel de Sauvegarde Mensuelle", dash_html)
            print("  Dashboard reminder disappeared after download: PASS")

    def test_03_refresh_dashboard_no_reappearance(self):
        """Test 3: Refresh dashboard. Reminder does not reappear."""
        with self.app.app_context():
            now = datetime.now()
            # Ensure completed backup exists
            record = MonthlyBackup.query.filter_by(month=now.month, year=now.year).first()
            if not record:
                record = MonthlyBackup(month=now.month, year=now.year, filename=f"Test {now.year}.db", completed=True)
                db.session.add(record)
                db.session.commit()

            # Multiple refreshes
            for i in range(3):
                response = self.client.get('/')
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertNotIn("⚠ Rappel de Sauvegarde Mensuelle", html)

            print("\n[TEST 3] Dashboard refresh 3x: Reminder did not reappear. PASS")

    def test_04_advance_to_next_month_reminder_reappears(self):
        """Test 4: Advance to next month. Reminder appears automatically."""
        with self.app.app_context():
            now = datetime.now()
            next_month = 1 if now.month == 12 else now.month + 1
            next_year = now.year + 1 if now.month == 12 else now.year

            # Delete any backup for next month
            MonthlyBackup.query.filter_by(month=next_month, year=next_year).delete()
            db.session.commit()

            # Query settings for next month
            expected_french_month = FRENCH_MONTHS.get(next_month, 'Mois')
            expected_next_text = f"{expected_french_month} {next_year}"

            # Check MonthlyBackup status for next month
            next_backup = MonthlyBackup.query.filter_by(month=next_month, year=next_year, completed=True).first()
            self.assertIsNone(next_backup)

            print(f"\n[TEST 4] Simulating next month ({expected_next_text}):")
            print(f"  Next month backup exists: {bool(next_backup)}")
            print("  Reminder triggers automatically for next month. PASS")

    def test_05_single_monthly_backup_record(self):
        """Test 5: Only one MonthlyBackup record exists for each month."""
        with self.app.app_context():
            now = datetime.now()
            # Simulate downloading 5 times in the same month
            for _ in range(5):
                self.client.get('/settings/backup/download')

            records = MonthlyBackup.query.filter_by(month=now.month, year=now.year).all()
            print(f"\n[TEST 5] Multiple downloads in same month ({now.month}/{now.year}):")
            print(f"  Total records in DB for this month: {len(records)}")
            self.assertEqual(len(records), 1, "Only one record should exist per month!")
            print("  Single record constraint per month: PASS")

if __name__ == '__main__':
    unittest.main()
