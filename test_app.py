import http.client
import json
import sqlite3
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path

import server


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(cls.temp_dir.name) / "test.sqlite3"
        server.initialize_database()
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.AppHandler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.httpd.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=3)
        cls.temp_dir.cleanup()

    def request(self, method, path, body=None, cookie=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if cookie:
            headers["Cookie"] = cookie
        connection.request(method, path, json.dumps(body) if body is not None else None, headers)
        response = connection.getresponse()
        payload = response.read()
        result = json.loads(payload) if "application/json" in response.getheader("Content-Type", "") else payload
        cookie_header = response.getheader("Set-Cookie")
        connection.close()
        return response.status, result, cookie_header

    def setUp(self):
        with server.database() as db:
            db.execute("DELETE FROM users")

    def test_authentication_and_complete_cash_basis_workflow(self):
        status, _, _ = self.request("GET", "/api/dashboard")
        self.assertEqual(status, 401)

        status, account, cookie = self.request("POST", "/api/register", {
            "name": "Alex Morgan", "email": "alex@example.com", "password": "secure-password-123",
        })
        self.assertEqual(status, 200)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)
        session_cookie = cookie.split(";", 1)[0]

        status, customer, _ = self.request("POST", "/api/customers", {
            "name": "Northstar Studio", "company": "Northstar", "email": "billing@northstar.test",
        }, session_cookie)
        self.assertEqual(status, 201)

        today = date.today()
        status, invoice, _ = self.request("POST", "/api/invoices", {
            "customer_id": customer["id"], "amount": "500.00",
            "issue_date": today.isoformat(), "due_date": (today + timedelta(days=14)).isoformat(),
            "description": "Website strategy", "service_category": "Web development", "status": "sent",
        }, session_cookie)
        self.assertEqual(status, 201)

        status, payment, _ = self.request("POST", "/api/payments", {
            "invoice_id": invoice["id"], "amount": "200.00",
            "paid_at": today.isoformat(), "method": "Bank transfer",
        }, session_cookie)
        self.assertEqual(status, 201)
        self.assertEqual(payment["remaining"], 300)

        status, _, _ = self.request("POST", "/api/payments", {
            "invoice_id": invoice["id"], "amount": "300.01",
            "paid_at": today.isoformat(), "method": "Bank transfer",
        }, session_cookie)
        self.assertEqual(status, 400)
        status, _, _ = self.request("POST", "/api/payments", {
            "invoice_id": invoice["id"], "amount": "1.00",
            "paid_at": (today + timedelta(days=1)).isoformat(), "method": "Bank transfer",
        }, session_cookie)
        self.assertEqual(status, 400)

        status, _, _ = self.request("POST", "/api/expenses", {
            "category": "Software", "description": "Design tools",
            "amount": "100.00", "expense_date": today.isoformat(),
        }, session_cookie)
        self.assertEqual(status, 201)

        status, dashboard, _ = self.request("GET", "/api/dashboard", cookie=session_cookie)
        self.assertEqual(status, 200)
        self.assertEqual(dashboard["revenue"], 200)
        self.assertEqual(dashboard["expenses"], 100)
        self.assertEqual(dashboard["profit"], 100)
        self.assertEqual(dashboard["outstanding"], 300)
        self.assertIsNone(dashboard["estimated_cash_balance"])

        status, settings, _ = self.request("PATCH", "/api/settings", {
            "business_name": "Northstar Studio", "currency": "USD",
            "opening_cash_balance": "500.00", "opening_balance_date": today.isoformat(),
        }, session_cookie)
        self.assertEqual(status, 200)
        self.assertEqual(settings["settings"]["opening_cash_balance"], 500)
        status, dashboard, _ = self.request("GET", "/api/dashboard", cookie=session_cookie)
        self.assertEqual(dashboard["estimated_cash_balance"], 600)
        self.assertFalse(dashboard["low_cash_balance"])
        status, _, _ = self.request("POST", "/api/expenses", {
            "category": "Contractors", "amount": "500.00",
            "expense_date": today.isoformat(), "service_category": "Web development",
        }, session_cookie)
        self.assertEqual(status, 201)
        status, dashboard, _ = self.request("GET", "/api/dashboard", cookie=session_cookie)
        self.assertEqual(dashboard["estimated_cash_balance"], 100)
        self.assertTrue(dashboard["low_cash_balance"])

        status, invoices, _ = self.request("GET", "/api/invoices", cookie=session_cookie)
        self.assertEqual(status, 200)
        self.assertEqual(invoices["invoices"][0]["balance"], 300)
        self.assertEqual(invoices["invoices"][0]["status"], "sent")

        status, draft, _ = self.request("POST", "/api/invoices", {
            "customer_id": customer["id"], "amount": "125.00",
            "issue_date": today.isoformat(), "due_date": (today + timedelta(days=14)).isoformat(),
            "status": "draft",
        }, session_cookie)
        self.assertEqual(status, 201)
        status, _, _ = self.request("PATCH", f"/api/invoices/{draft['id']}", {
            "status": "sent",
        }, session_cookie)
        self.assertEqual(status, 200)
        status, invoices, _ = self.request("GET", "/api/invoices", cookie=session_cookie)
        self.assertEqual(status, 200)
        draft = next(item for item in invoices["invoices"] if item["id"] == draft["id"])
        self.assertEqual(draft["status"], "sent")
        status, _, _ = self.request("PATCH", f"/api/invoices/{draft['id']}", {
            "status": "sent",
        }, session_cookie)
        self.assertEqual(status, 409)

        status, insights, _ = self.request("GET", "/api/insights", cookie=session_cookie)
        self.assertEqual(status, 200)
        self.assertEqual(insights["insights"]["financial_summary"]["outstanding_invoices"], 425)
        self.assertIsNone(insights["insights"]["financial_summary"]["revenue_growth_percent"])
        self.assertEqual(
            insights["insights"]["financial_summary"]["service_contribution_before_shared_costs"][0]
            ["contribution_before_shared_costs"], -300)
        self.assertTrue(insights["insights"]["performance"])

        status, _, _ = self.request("POST", "/api/reminders", {
            "invoice_id": invoice["id"],
        }, session_cookie)
        self.assertEqual(status, 201)
        status, reminders, _ = self.request("GET", "/api/reminders", cookie=session_cookie)
        self.assertEqual(status, 200)
        self.assertEqual(reminders["reminders"][0]["reminder_count"], 1)

        status, report, _ = self.request("GET", "/api/reports.csv", cookie=session_cookie)
        self.assertEqual(status, 200)
        self.assertIn(b"Collected revenue", report)
        self.assertIn(b"600.0", report)
        self.assertIn(b"-400.0", report)
        self.assertIn(f"{today.strftime('%b')} {today.year}".encode(), report)

        status, _, _ = self.request("POST", "/api/insights/gemini", {}, session_cookie)
        self.assertEqual(status, 503)

        status, other_user, other_cookie = self.request("POST", "/api/register", {
            "name": "Jamie Lee", "email": "jamie@example.com", "password": "another-secure-password",
        })
        self.assertEqual(status, 200)
        status, other_invoices, _ = self.request(
            "GET", "/api/invoices", cookie=other_cookie.split(";", 1)[0])
        self.assertEqual(status, 200)
        self.assertEqual(other_invoices["invoices"], [])

    def test_invalid_records_are_rejected_without_database_changes(self):
        status, _, cookie = self.request("POST", "/api/register", {
            "name": "Taylor", "email": "taylor@example.com", "password": "secure-password-123",
        })
        self.assertEqual(status, 200)
        session_cookie = cookie.split(";", 1)[0]

        status, _, _ = self.request("POST", "/api/customers", {
            "name": "Taylor Client", "email": "not-an-email",
        }, session_cookie)
        self.assertEqual(status, 400)

        status, _, _ = self.request("POST", "/api/expenses", {
            "category": "Software", "amount": "-12", "expense_date": "2026-03-99",
        }, session_cookie)
        self.assertEqual(status, 400)
        status, _, _ = self.request("POST", "/api/expenses", {
            "category": "Software", "amount": "12.00",
            "expense_date": (date.today() + timedelta(days=1)).isoformat(),
        }, session_cookie)
        self.assertEqual(status, 400)

        status, expenses, _ = self.request("GET", "/api/expenses", cookie=session_cookie)
        self.assertEqual(status, 200)
        self.assertEqual(expenses["expenses"], [])

    def test_existing_settings_are_migrated_without_losing_business_preferences(self):
        previous_path = server.DB_PATH
        with tempfile.TemporaryDirectory() as migration_dir:
            try:
                server.DB_PATH = Path(migration_dir) / "legacy.sqlite3"
                legacy_db = sqlite3.connect(server.DB_PATH)
                try:
                    legacy_db.execute(
                        """CREATE TABLE users (
                           id INTEGER PRIMARY KEY,name TEXT,email TEXT,password_hash TEXT,password_salt TEXT
                           )"""
                    )
                    legacy_db.execute("INSERT INTO users VALUES(1,'Legacy owner','legacy@example.test','hash','salt')")
                    legacy_db.execute(
                        """CREATE TABLE settings (
                           user_id INTEGER PRIMARY KEY REFERENCES users(id),
                           business_name TEXT NOT NULL DEFAULT '',
                           currency TEXT NOT NULL DEFAULT 'USD'
                           )"""
                    )
                    legacy_db.execute(
                        "INSERT INTO settings(user_id,business_name,currency) VALUES(1,'Legacy Studio','CAD')"
                    )
                    legacy_db.commit()
                finally:
                    legacy_db.close()

                server.initialize_database()
                with server.database() as db:
                    columns = {row["name"] for row in db.execute("PRAGMA table_info(settings)")}
                    settings = server.user_settings(db, 1)

                self.assertIn("opening_cash_balance", columns)
                self.assertIn("opening_balance_date", columns)
                self.assertEqual(settings["business_name"], "Legacy Studio")
                self.assertEqual(settings["currency"], "CAD")
                self.assertIsNone(settings["opening_cash_balance"])
            finally:
                server.DB_PATH = previous_path


if __name__ == "__main__":
    unittest.main()
