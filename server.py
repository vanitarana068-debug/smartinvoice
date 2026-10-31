import csv
import hashlib
import hmac
import io
import json
import logging
import os
import re
import secrets
import sqlite3
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
DB_PATH = Path(os.environ.get("SMART_INVOICE_DB", str(ROOT / "data" / "smart-invoice.db")))
SESSION_DAYS = 30
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class APIError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 10000")
    return db


@contextmanager
def database():
    db = connect()
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize_database():
    with database() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                business_name TEXT NOT NULL DEFAULT '',
                currency TEXT NOT NULL DEFAULT 'USD',
                opening_cash_balance REAL,
                opening_balance_date TEXT NOT NULL DEFAULT '1970-01-01'
            );
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                company TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
                number TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                amount REAL NOT NULL CHECK (amount > 0),
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('draft', 'sent', 'paid', 'overdue')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                service_category TEXT NOT NULL DEFAULT 'General services',
                UNIQUE(user_id, number)
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                amount REAL NOT NULL CHECK (amount > 0),
                expense_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                service_category TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
                amount REAL NOT NULL CHECK (amount > 0),
                paid_at TEXT NOT NULL,
                method TEXT NOT NULL DEFAULT 'Bank transfer',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
                sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_customers_user ON customers(user_id);
            CREATE INDEX IF NOT EXISTS idx_invoices_user_dates ON invoices(user_id, issue_date, due_date);
            CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, expense_date);
            CREATE INDEX IF NOT EXISTS idx_payments_user_date ON payments(user_id, paid_at);
            CREATE INDEX IF NOT EXISTS idx_reminders_user_invoice ON reminders(user_id, invoice_id);
            """
        )
        for table, column, definition in (
            ("invoices", "service_category", "TEXT NOT NULL DEFAULT 'General services'"),
            ("expenses", "service_category", "TEXT NOT NULL DEFAULT ''"),
            ("settings", "opening_cash_balance", "REAL"),
            ("settings", "opening_balance_date", "TEXT NOT NULL DEFAULT '1970-01-01'"),
        ):
            columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
            if column not in columns:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def money_to_cents(value):
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        raise APIError(400, "Enter a valid amount.")
    if not amount.is_finite() or amount <= 0 or amount > Decimal("999999999.99"):
        raise APIError(400, "Enter an amount greater than zero and below 1 billion.")
    return int(amount * 100)


def signed_money_to_cents(value):
    try:
        balance = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        raise APIError(400, "Enter a valid opening balance.")
    if not balance.is_finite() or abs(balance) > Decimal("999999999.99"):
        raise APIError(400, "Opening balance must be between -1 billion and 1 billion.")
    return int(balance * 100)


def cents(value):
    return int((Decimal(str(value or 0)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def amount(cents_value):
    return round(cents_value / 100, 2)


def valid_date(value, field):
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        raise APIError(400, f"Enter a valid {field.lower()}.")


def month_start(value):
    return value.replace(day=1)


def shift_month(value, delta):
    index = value.year * 12 + value.month - 1 + delta
    return date(index // 12, index % 12 + 1, 1)


def user_settings(db, user_id):
    row = db.execute(
        """SELECT business_name,currency,opening_cash_balance,opening_balance_date
           FROM settings WHERE user_id = ?""", (user_id,)
    ).fetchone()
    settings = dict(row) if row else {
        "business_name": "", "currency": "USD", "opening_cash_balance": None,
        "opening_balance_date": date.today().isoformat(),
    }
    if not settings["opening_balance_date"] or (
        settings["opening_balance_date"] == "1970-01-01"
        and settings["opening_cash_balance"] is None
    ):
        settings["opening_balance_date"] = date.today().isoformat()
    return settings


def effective_status(invoice, paid_cents, today=None):
    if invoice["status"] == "draft":
        return "draft"
    if paid_cents >= cents(invoice["amount"]):
        return "paid"
    if invoice["due_date"] < (today or date.today()).isoformat():
        return "overdue"
    return "sent"


class AppHandler(BaseHTTPRequestHandler):
    server_version = "SmartInvoice/1.0"

    def log_message(self, fmt, *args):
        logging.info("%s - %s", self.address_string(), fmt % args)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        self.wfile.write(body)

    def fail(self, error):
        self.send_json(error.status, {"error": error.message})

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise APIError(400, "Invalid request size.")
        if length > 1_000_000:
            raise APIError(413, "Request is too large.")
        if length <= 0:
            return {}
        try:
            data = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise APIError(400, "Request body must be valid JSON.")
        if not isinstance(data, dict):
            raise APIError(400, "Request body must be a JSON object.")
        return data

    def authenticated_user(self, db):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except (CookieError, ValueError):
            raise APIError(401, "Please sign in to continue.")
        morsel = cookie.get("smart_invoice_session")
        if morsel is None:
            raise APIError(401, "Please sign in to continue.")
        token_hash = hashlib.sha256(morsel.value.encode()).hexdigest()
        row = db.execute(
            """SELECT u.id, u.name, u.email FROM sessions s
               JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > ?""",
            (token_hash, int(datetime.now(timezone.utc).timestamp())),
        ).fetchone()
        if row is None:
            raise APIError(401, "Your session has expired. Please sign in again.")
        return dict(row)

    def session_cookie(self, token, max_age):
        secure = "; Secure" if os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "yes") else ""
        return (
            f"smart_invoice_session={token}; Path=/; HttpOnly; SameSite=Lax; "
            f"Max-Age={max_age}{secure}"
        )

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self.static_file("index.html")
        if parsed.path in ("/app.js", "/styles.css"):
            return self.static_file(parsed.path.lstrip("/"))
        if not parsed.path.startswith("/api/"):
            return self.send_json(404, {"error": "Not found."})
        try:
            with database() as db:
                if parsed.path == "/api/health":
                    self.send_json(200, {"ok": True})
                    return
                user = self.authenticated_user(db)
                user_id = user["id"]
                if parsed.path == "/api/me":
                    self.send_json(200, {"user": user, "settings": user_settings(db, user_id),
                                         "aiAvailable": bool(os.environ.get("GEMINI_API_KEY"))})
                elif parsed.path == "/api/dashboard":
                    self.send_json(200, dashboard(db, user_id))
                elif parsed.path == "/api/invoices":
                    self.send_json(200, {"invoices": invoice_list(db, user_id)})
                elif parsed.path == "/api/customers":
                    self.send_json(200, {"customers": customer_list(db, user_id)})
                elif parsed.path == "/api/expenses":
                    self.send_json(200, {"expenses": expense_list(db, user_id)})
                elif parsed.path == "/api/payments":
                    self.send_json(200, {"payments": payment_list(db, user_id)})
                elif parsed.path == "/api/analytics":
                    self.send_json(200, analytics(db, user_id))
                elif parsed.path == "/api/reminders":
                    self.send_json(200, {"reminders": reminder_list(db, user_id)})
                elif parsed.path == "/api/settings":
                    self.send_json(200, {"settings": user_settings(db, user_id)})
                elif parsed.path == "/api/insights":
                    self.send_json(200, {"insights": local_insights(db, user_id),
                                         "aiAvailable": bool(os.environ.get("GEMINI_API_KEY"))})
                elif parsed.path == "/api/reports.csv":
                    self.send_report(db, user_id)
                else:
                    self.send_json(404, {"error": "Not found."})
        except APIError as error:
            self.fail(error)
        except sqlite3.Error:
            logging.exception("Database error handling %s", parsed.path)
            self.send_json(500, {"error": "A database error occurred. Please try again."})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            data = self.read_json()
            with database() as db:
                if parsed.path == "/api/register":
                    self.register(db, data)
                elif parsed.path == "/api/login":
                    self.login(db, data)
                elif parsed.path == "/api/logout":
                    morsel = self.request_cookie()
                    if morsel:
                        db.execute("DELETE FROM sessions WHERE token_hash = ?",
                                   (hashlib.sha256(morsel.encode()).hexdigest(),))
                    self.send_response(204)
                    self.send_header("Set-Cookie", self.session_cookie("", 0))
                    self.end_headers()
                else:
                    user = self.authenticated_user(db)
                    user_id = user["id"]
                    if parsed.path == "/api/customers":
                        self.create_customer(db, user_id, data)
                    elif parsed.path == "/api/invoices":
                        self.create_invoice(db, user_id, data)
                    elif parsed.path == "/api/expenses":
                        self.create_expense(db, user_id, data)
                    elif parsed.path == "/api/payments":
                        self.create_payment(db, user_id, data)
                    elif parsed.path == "/api/reminders":
                        self.create_reminder(db, user_id, data)
                    elif parsed.path == "/api/settings":
                        self.update_settings(db, user_id, data)
                    elif parsed.path == "/api/insights/gemini":
                        self.generate_gemini_insights(db, user_id)
                    else:
                        self.send_json(404, {"error": "Not found."})
        except APIError as error:
            self.fail(error)
        except sqlite3.IntegrityError as error:
            logging.info("Rejected invalid financial record: %s", error)
            message = "That invoice number is already in use." if "invoices.user_id, invoices.number" in str(error) else "This record conflicts with existing business records."
            self.send_json(409, {"error": message})
        except sqlite3.Error:
            logging.exception("Database error handling %s", parsed.path)
            self.send_json(500, {"error": "A database error occurred. Please try again."})

    def do_PATCH(self):
        parsed = urlparse(self.path)
        try:
            data = self.read_json()
            with database() as db:
                user_id = self.authenticated_user(db)["id"]
                if parsed.path == "/api/settings":
                    self.update_settings(db, user_id, data)
                elif parsed.path.startswith("/api/invoices/"):
                    self.update_invoice(db, user_id, parsed.path.rsplit("/", 1)[-1], data)
                elif parsed.path.startswith("/api/customers/"):
                    self.update_customer(db, user_id, parsed.path.rsplit("/", 1)[-1], data)
                else:
                    self.send_json(404, {"error": "Not found."})
        except APIError as error:
            self.fail(error)
        except sqlite3.Error:
            logging.exception("Database error handling %s", parsed.path)
            self.send_json(500, {"error": "A database error occurred. Please try again."})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        try:
            with database() as db:
                user_id = self.authenticated_user(db)["id"]
                if parsed.path.startswith("/api/customers/"):
                    customer_id = parse_id(parsed.path.rsplit("/", 1)[-1])
                    cursor = db.execute("DELETE FROM customers WHERE id = ? AND user_id = ?",
                                        (customer_id, user_id))
                    if cursor.rowcount == 0:
                        raise APIError(404, "Customer not found.")
                elif parsed.path.startswith("/api/expenses/"):
                    expense_id = parse_id(parsed.path.rsplit("/", 1)[-1])
                    cursor = db.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?",
                                        (expense_id, user_id))
                    if cursor.rowcount == 0:
                        raise APIError(404, "Expense not found.")
                elif parsed.path.startswith("/api/invoices/"):
                    invoice_id = parse_id(parsed.path.rsplit("/", 1)[-1])
                    cursor = db.execute(
                        "DELETE FROM invoices WHERE id = ? AND user_id = ? AND status = 'draft' AND NOT EXISTS (SELECT 1 FROM payments WHERE payments.invoice_id = invoices.id)",
                        (invoice_id, user_id))
                    if cursor.rowcount == 0:
                        raise APIError(409, "Only draft invoices without payments can be deleted.")
                else:
                    self.send_json(404, {"error": "Not found."})
                    return
                self.send_json(200, {"ok": True})
        except APIError as error:
            self.fail(error)
        except sqlite3.IntegrityError:
            self.send_json(409, {"error": "This customer has invoices and cannot be deleted."})
        except sqlite3.Error:
            logging.exception("Database error handling %s", parsed.path)
            self.send_json(500, {"error": "A database error occurred. Please try again."})

    def request_cookie(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
        except (CookieError, ValueError):
            return None
        item = cookies.get("smart_invoice_session")
        return item.value if item else None

    def static_file(self, name):
        path = (PUBLIC / name).resolve()
        if not path.is_relative_to(PUBLIC.resolve()) or not path.is_file():
            return self.send_json(404, {"error": "Not found."})
        content_type = "text/html; charset=utf-8" if name.endswith(".html") else (
            "text/javascript; charset=utf-8" if name.endswith(".js") else "text/css; charset=utf-8"
        )
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com data:; img-src 'self' data:; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def register(self, db, data):
        name = clean_text(data.get("name"), "Name", 80)
        email = clean_email(data.get("email"))
        password = data.get("password")
        if not isinstance(password, str) or len(password) < 8 or len(password) > 256:
            raise APIError(400, "Password must be between 8 and 256 characters.")
        if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            raise APIError(409, "An account with that email already exists.")
        salt = secrets.token_bytes(16)
        password_hash = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1).hex()
        cur = db.execute("INSERT INTO users(name,email,password_hash,password_salt) VALUES(?,?,?,?)",
                         (name, email, password_hash, salt.hex()))
        user_id = cur.lastrowid
        db.execute("INSERT INTO settings(user_id, business_name, currency) VALUES(?, ?, 'USD')",
                   (user_id, name + "'s business"))
        self.finish_login(db, user_id, name, email)

    def login(self, db, data):
        email = clean_email(data.get("email"))
        password = data.get("password")
        if not isinstance(password, str) or len(password) > 256:
            raise APIError(401, "Email or password is incorrect.")
        row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not row:
            raise APIError(401, "Email or password is incorrect.")
        candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(row["password_salt"]),
                                   n=2**14, r=8, p=1).hex()
        if not hmac.compare_digest(candidate, row["password_hash"]):
            raise APIError(401, "Email or password is incorrect.")
        self.finish_login(db, row["id"], row["name"], row["email"])

    def finish_login(self, db, user_id, name, email):
        token = secrets.token_urlsafe(32)
        expiry = int(datetime.now(timezone.utc).timestamp()) + SESSION_DAYS * 86400
        db.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)",
                   (hashlib.sha256(token.encode()).hexdigest(), user_id, expiry))
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Set-Cookie", self.session_cookie(token, SESSION_DAYS * 86400))
        body = json.dumps({"user": {"id": user_id, "name": name, "email": email},
                           "settings": user_settings(db, user_id)}).encode()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def create_customer(self, db, user_id, data):
        name = clean_text(data.get("name"), "Customer name", 120)
        email = clean_email(data.get("email"), required=False)
        company = clean_text(data.get("company", ""), "Company", 120, required=False)
        cursor = db.execute("INSERT INTO customers(user_id,name,email,company) VALUES(?,?,?,?)",
                            (user_id, name, email, company))
        self.send_json(201, {"id": cursor.lastrowid})

    def update_customer(self, db, user_id, raw_id, data):
        customer_id = parse_id(raw_id)
        name = clean_text(data.get("name"), "Customer name", 120)
        email = clean_email(data.get("email"), required=False)
        company = clean_text(data.get("company", ""), "Company", 120, required=False)
        cursor = db.execute("UPDATE customers SET name=?,email=?,company=? WHERE id=? AND user_id=?",
                            (name, email, company, customer_id, user_id))
        if cursor.rowcount == 0:
            raise APIError(404, "Customer not found.")
        self.send_json(200, {"ok": True})

    def update_invoice(self, db, user_id, raw_id, data):
        invoice_id = parse_id(raw_id)
        if data.get("status") != "sent":
            raise APIError(400, "A draft invoice can only be marked as sent.")
        cursor = db.execute(
            "UPDATE invoices SET status='sent' WHERE id=? AND user_id=? AND status='draft'",
            (invoice_id, user_id))
        if cursor.rowcount == 0:
            exists = db.execute(
                "SELECT 1 FROM invoices WHERE id=? AND user_id=?", (invoice_id, user_id)
            ).fetchone()
            if not exists:
                raise APIError(404, "Invoice not found.")
            raise APIError(409, "Only draft invoices can be marked as sent.")
        self.send_json(200, {"ok": True})

    def create_invoice(self, db, user_id, data):
        customer_id = parse_id(data.get("customer_id"))
        customer = db.execute("SELECT id FROM customers WHERE id=? AND user_id=?",
                              (customer_id, user_id)).fetchone()
        if not customer:
            raise APIError(400, "Choose one of your customers.")
        total = money_to_cents(data.get("amount"))
        issue = valid_date(data.get("issue_date", date.today().isoformat()), "Issue date")
        due = valid_date(data.get("due_date"), "due date")
        if due < issue:
            raise APIError(400, "The due date cannot be before the issue date.")
        raw_number = data.get("number")
        if raw_number:
            number = clean_text(raw_number, "Invoice number", 40)
        else:
            number = f"INV-{issue.year}-{db.execute('SELECT COALESCE(MAX(id),0)+1 FROM invoices').fetchone()[0]:04d}"
        status = data.get("status", "sent")
        if status not in ("draft", "sent"):
            raise APIError(400, "New invoices must be drafts or sent.")
        description = clean_text(data.get("description", ""), "Description", 500, required=False)
        category = clean_text(data.get("service_category", "General services"),
                              "Service category", 80, required=False) or "General services"
        cursor = db.execute(
            """INSERT INTO invoices(user_id,customer_id,number,description,amount,issue_date,
               due_date,status,service_category) VALUES(?,?,?,?,?,?,?,?,?)""",
            (user_id, customer_id, number, description, amount(total),
             issue.isoformat(), due.isoformat(), status, category))
        self.send_json(201, {"id": cursor.lastrowid, "number": number})

    def create_expense(self, db, user_id, data):
        category = clean_text(data.get("category"), "Category", 80)
        description = clean_text(data.get("description", ""), "Description", 500, required=False)
        service_category = clean_text(data.get("service_category", ""), "Service category", 80, required=False)
        total = money_to_cents(data.get("amount"))
        expense_date = valid_date(data.get("expense_date", date.today().isoformat()), "expense date")
        if expense_date > date.today():
            raise APIError(400, "An expense date cannot be in the future.")
        cursor = db.execute(
            """INSERT INTO expenses(user_id,category,description,amount,expense_date,service_category)
               VALUES(?,?,?,?,?,?)""",
            (user_id, category, description, amount(total), expense_date.isoformat(), service_category))
        self.send_json(201, {"id": cursor.lastrowid})

    def create_payment(self, db, user_id, data):
        invoice_id = parse_id(data.get("invoice_id"))
        invoice = db.execute("SELECT * FROM invoices WHERE id=? AND user_id=?",
                             (invoice_id, user_id)).fetchone()
        if not invoice:
            raise APIError(404, "Invoice not found.")
        if invoice["status"] == "draft":
            raise APIError(400, "Send the draft invoice before recording a payment.")
        paid = db.execute("SELECT COALESCE(SUM(amount),0) AS value FROM payments WHERE invoice_id=?",
                          (invoice_id,)).fetchone()["value"]
        remaining = cents(invoice["amount"]) - cents(paid)
        total = money_to_cents(data.get("amount"))
        if total > remaining:
            raise APIError(400, f"Payment exceeds the remaining balance of {amount(remaining):.2f}.")
        paid_at = valid_date(data.get("paid_at", date.today().isoformat()), "payment date")
        if paid_at > date.today():
            raise APIError(400, "A payment date cannot be in the future.")
        method = clean_text(data.get("method", "Bank transfer"), "Payment method", 60)
        cursor = db.execute("INSERT INTO payments(user_id,invoice_id,amount,paid_at,method) VALUES(?,?,?,?,?)",
                            (user_id, invoice_id, amount(total), paid_at.isoformat(), method))
        self.send_json(201, {"id": cursor.lastrowid, "invoice_id": invoice_id,
                             "remaining": amount(remaining - total)})

    def create_reminder(self, db, user_id, data):
        invoice_id = parse_id(data.get("invoice_id"))
        invoice = db.execute(
            "SELECT id,status,due_date,amount FROM invoices WHERE id=? AND user_id=?",
            (invoice_id, user_id)).fetchone()
        if not invoice:
            raise APIError(404, "Invoice not found.")
        paid = db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?",
                          (invoice_id,)).fetchone()[0]
        if invoice["status"] == "draft" or cents(paid) >= cents(invoice["amount"]):
            raise APIError(400, "Only sent invoices with a balance need payment reminders.")
        db.execute("INSERT INTO reminders(user_id,invoice_id) VALUES(?,?)", (user_id, invoice_id))
        self.send_json(201, {"ok": True})

    def update_settings(self, db, user_id, data):
        business_name = clean_text(data.get("business_name"), "Business name", 120)
        currency = str(data.get("currency", "")).upper()
        if not CURRENCY_RE.fullmatch(currency):
            raise APIError(400, "Choose a valid three-letter currency code.")
        current = user_settings(db, user_id)
        raw_balance = data.get("opening_cash_balance", current["opening_cash_balance"])
        opening_balance = None if raw_balance is None or raw_balance == "" else amount(
            signed_money_to_cents(raw_balance)
        )
        raw_date = data.get("opening_balance_date", current["opening_balance_date"])
        opening_date = valid_date(raw_date, "opening balance date")
        if opening_date > date.today():
            raise APIError(400, "The opening balance date cannot be in the future.")
        db.execute(
            """INSERT INTO settings(user_id,business_name,currency,opening_cash_balance,opening_balance_date)
               VALUES(?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET business_name=excluded.business_name,
               currency=excluded.currency,opening_cash_balance=excluded.opening_cash_balance,
               opening_balance_date=excluded.opening_balance_date""",
            (user_id, business_name, currency, opening_balance, opening_date.isoformat()))
        self.send_json(200, {"settings": user_settings(db, user_id)})

    def send_report(self, db, user_id):
        settings = user_settings(db, user_id)
        result = analytics(db, user_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Smart Invoice AI — Cash Flow Report", settings["business_name"]])
        writer.writerow(["Period", "Currency", "Collected revenue", "Expenses", "Net cash flow"])
        for row in result["months"]:
            writer.writerow([f"{row['month']} {row['year']}", settings["currency"],
                             row["revenue"], row["expenses"], row["net"]])
        writer.writerow([])
        writer.writerow(["Generated", date.today().isoformat()])
        body = output.getvalue().encode("utf-8-sig")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="smart-invoice-cash-flow.csv"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def generate_gemini_insights(self, db, user_id):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise APIError(503, "Gemini is not connected yet. Set GEMINI_API_KEY on the server and restart the app.")
        summary = local_insights(db, user_id)
        # Send only aggregated financial metrics; customer names, contact details, and raw records stay local.
        prompt = (
            "You are a careful small-business finance analyst. Analyze this cash-basis financial summary. "
            "Do not give tax, legal, or investment advice. Never invent figures. Clearly distinguish "
            "observations from recommendations. Return strict JSON with exactly these keys: "
            '{"performance":["..."],"warnings":["..."],"opportunities":["..."],"outlook":"..."}. '
            "Use concise, specific language. Currency is included in the figures.\n"
            + json.dumps(summary["financial_summary"], separators=(",", ":"))
        )
        request_body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
        }).encode()
        request = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            data=request_body, headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                result = json.loads(response.read(1_000_000))
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            generated = json.loads(text)
            for key in ("performance", "warnings", "opportunities"):
                if not isinstance(generated.get(key), list) or not all(
                    isinstance(item, str) for item in generated[key]
                ):
                    raise ValueError(f"Gemini returned an invalid {key} list")
            if not isinstance(generated.get("outlook"), str):
                raise ValueError("Gemini returned an invalid outlook")
        except urllib.error.HTTPError as error:
            logging.error("Gemini API returned HTTP %s", error.code)
            raise APIError(502, "Gemini could not complete the analysis. Check the server API key and try again.")
        except (urllib.error.URLError, TimeoutError):
            logging.exception("Gemini API request failed")
            raise APIError(502, "Gemini is temporarily unavailable. Please try again.")
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError):
            logging.exception("Gemini returned an invalid response")
            raise APIError(502, "Gemini returned an invalid analysis. Please try again.")
        self.send_json(200, {"analysis": generated, "generated_at": datetime.now(timezone.utc).isoformat()})


def parse_id(value):
    try:
        result = int(value)
    except (ValueError, TypeError):
        raise APIError(400, "A valid record ID is required.")
    if result <= 0:
        raise APIError(400, "A valid record ID is required.")
    return result


def clean_text(value, label, maximum, required=True):
    if not isinstance(value, str):
        if value is None and not required:
            return ""
        raise APIError(400, f"{label} is required." if required else f"{label} must be text.")
    value = value.strip()
    if required and not value:
        raise APIError(400, f"{label} is required.")
    if len(value) > maximum:
        raise APIError(400, f"{label} must be {maximum} characters or fewer.")
    return value


def clean_email(value, required=True):
    if value is None and not required:
        return ""
    email = clean_text(value, "Email", 254, required=required).lower()
    if email and not EMAIL_RE.fullmatch(email):
        raise APIError(400, "Enter a valid email address.")
    return email


def customer_list(db, user_id):
    return [dict(row) for row in db.execute(
        """SELECT c.id,c.name,c.email,c.company,c.created_at,
           (SELECT COUNT(*) FROM invoices ci WHERE ci.customer_id=c.id AND ci.user_id=c.user_id) AS invoice_count,
           COALESCE((SELECT SUM(ci.amount) FROM invoices ci
                     WHERE ci.customer_id=c.id AND ci.user_id=c.user_id),0) AS invoiced,
           COALESCE((SELECT SUM(p.amount) FROM payments p
                     JOIN invoices pi ON pi.id=p.invoice_id
                     WHERE pi.customer_id=c.id AND p.user_id=c.user_id),0) AS collected
           FROM customers c WHERE c.user_id=? ORDER BY c.name COLLATE NOCASE""", (user_id,))]


def invoice_list(db, user_id):
    rows = db.execute(
        """SELECT i.*,c.name AS customer_name,c.email AS customer_email,c.company AS customer_company,
           COALESCE((SELECT SUM(p.amount) FROM payments p
                     WHERE p.invoice_id=i.id AND p.user_id=i.user_id),0) AS paid_amount
           FROM invoices i JOIN customers c ON c.id=i.customer_id AND c.user_id=i.user_id
           WHERE i.user_id=? ORDER BY i.issue_date DESC,i.id DESC""", (user_id,))
    result = []
    today = date.today()
    for row in rows:
        item = dict(row)
        paid = cents(row["paid_amount"])
        item["paid_amount"] = amount(paid)
        item["balance"] = amount(max(0, cents(row["amount"]) - paid))
        item["status"] = effective_status(row, paid, today)
        result.append(item)
    return result


def expense_list(db, user_id):
    return [dict(row) for row in db.execute(
        "SELECT * FROM expenses WHERE user_id=? ORDER BY expense_date DESC,id DESC", (user_id,))]


def payment_list(db, user_id):
    return [dict(row) for row in db.execute(
        """SELECT p.id,p.invoice_id,p.amount,p.paid_at,p.method,c.name AS customer_name,
           i.number AS invoice_number FROM payments p
           JOIN invoices i ON i.id=p.invoice_id AND i.user_id=p.user_id
           JOIN customers c ON c.id=i.customer_id AND c.user_id=i.user_id
           WHERE p.user_id=? ORDER BY p.paid_at DESC,p.id DESC""", (user_id,))]


def reminder_list(db, user_id):
    results = []
    for invoice in invoice_list(db, user_id):
        if invoice["status"] == "draft":
            continue
        reminder = db.execute(
            """SELECT COUNT(*) AS count, MAX(sent_at) AS latest FROM reminders
               WHERE user_id=? AND invoice_id=?""", (user_id, invoice["id"])).fetchone()
        results.append({
            "id": invoice["id"], "customer_name": invoice["customer_name"],
            "number": invoice["number"], "due_date": invoice["due_date"],
            "balance": invoice["balance"], "status": invoice["status"],
            "last_reminder": reminder["latest"], "reminder_count": reminder["count"],
        })
    return sorted(results, key=lambda item: (
        item["status"] != "overdue", item["due_date"], item["number"]
    ))


def dashboard(db, user_id):
    today = date.today()
    start = month_start(today).isoformat()
    next_month = shift_month(today, 1).isoformat()
    revenue = cents(db.execute(
        "SELECT COALESCE(SUM(amount),0) FROM payments WHERE user_id=? AND paid_at>=? AND paid_at<?",
        (user_id, start, next_month)).fetchone()[0])
    expenses = cents(db.execute(
        "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND expense_date>=? AND expense_date<?",
        (user_id, start, next_month)).fetchone()[0])
    prev_start = shift_month(today, -1).isoformat()
    prev_revenue = cents(db.execute(
        "SELECT COALESCE(SUM(amount),0) FROM payments WHERE user_id=? AND paid_at>=? AND paid_at<?",
        (user_id, prev_start, start)).fetchone()[0])
    prev_expenses = cents(db.execute(
        "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND expense_date>=? AND expense_date<?",
        (user_id, prev_start, start)).fetchone()[0])
    invoices = invoice_list(db, user_id)
    financial_data = analytics(db, user_id)
    outstanding = sum(cents(item["balance"]) for item in invoices if item["status"] != "draft")
    overdue = [item for item in invoices if item["status"] == "overdue"]
    recent = db.execute(
        """SELECT 'payment' AS type,p.id,p.amount,p.paid_at AS date,c.name AS label,
           i.number AS detail FROM payments p
           JOIN invoices i ON i.id=p.invoice_id AND i.user_id=p.user_id
           JOIN customers c ON c.id=i.customer_id AND c.user_id=i.user_id
           WHERE p.user_id=?
           UNION ALL
           SELECT 'expense' AS type,e.id,e.amount,e.expense_date AS date,e.category AS label,
           e.description AS detail FROM expenses e WHERE e.user_id=?
           ORDER BY date DESC,id DESC LIMIT 8""", (user_id, user_id)).fetchall()
    return {
        "currency": user_settings(db, user_id)["currency"],
        "month": today.strftime("%B %Y"),
        "revenue": amount(revenue), "expenses": amount(expenses),
        "profit": amount(revenue - expenses),
        "revenue_change": growth(revenue, prev_revenue),
        "expense_change": growth(expenses, prev_expenses),
        "outstanding": amount(outstanding), "overdue_count": len(overdue),
        "overdue_amount": amount(sum(cents(i["balance"]) for i in overdue)),
        "invoice_count": len([item for item in invoices if item["status"] != "draft"]),
        "customer_count": db.execute("SELECT COUNT(*) FROM customers WHERE user_id=?",
                                     (user_id,)).fetchone()[0],
        "months": financial_data["months"],
        "estimated_cash_balance": financial_data["estimated_cash_balance"],
        "low_cash_balance": financial_data["low_cash_balance"],
        "recent": [dict(row) for row in recent],
        "top_customers": sorted(customer_list(db, user_id),
                                key=lambda item: item["collected"], reverse=True)[:5],
        "attention": overdue[:5],
    }


def growth(current, previous):
    if not previous:
        return None if current else 0
    return round((current - previous) / previous * 100, 1)


def growth_description(label, current, previous):
    change = growth(current, previous)
    if change is None:
        return f"{label} growth is not comparable yet because the previous period had no recorded activity."
    return f"{label} changed {change:+.1f}% between the first and last three months."


def analytics(db, user_id):
    today = date.today()
    first = shift_month(month_start(today), -5)
    months = []
    for offset in range(6):
        start = shift_month(first, offset)
        end = shift_month(start, 1)
        revenue = cents(db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM payments WHERE user_id=? AND paid_at>=? AND paid_at<?",
            (user_id, start.isoformat(), end.isoformat())).fetchone()[0])
        expenses = cents(db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND expense_date>=? AND expense_date<?",
            (user_id, start.isoformat(), end.isoformat())).fetchone()[0])
        months.append({"month": start.strftime("%b"), "year": start.year,
                       "revenue": amount(revenue), "expenses": amount(expenses),
                       "net": amount(revenue - expenses)})
    latest_expenses = sum(cents(item["expenses"]) for item in months[-3:])
    average_monthly_expenses = amount(round(latest_expenses / 3))
    cash_balance = cash_position(db, user_id)
    return {
        "currency": user_settings(db, user_id)["currency"],
        "months": months,
        "estimated_cash_balance": cash_balance,
        "average_monthly_expenses": average_monthly_expenses,
        "low_cash_balance": cash_balance is not None and cash_balance < average_monthly_expenses,
    }


def cash_position(db, user_id):
    settings = user_settings(db, user_id)
    if settings["opening_cash_balance"] is None:
        return None
    opening_date = valid_date(settings["opening_balance_date"], "opening balance date").isoformat()
    today = date.today().isoformat()
    incoming = db.execute(
        """SELECT COALESCE(SUM(amount),0) FROM payments
           WHERE user_id=? AND paid_at>=? AND paid_at<=?""",
        (user_id, opening_date, today)).fetchone()[0]
    outgoing = db.execute(
        """SELECT COALESCE(SUM(amount),0) FROM expenses
           WHERE user_id=? AND expense_date>=? AND expense_date<=?""",
        (user_id, opening_date, today)).fetchone()[0]
    return amount(cents(settings["opening_cash_balance"]) + cents(incoming) - cents(outgoing))


def local_insights(db, user_id):
    settings = user_settings(db, user_id)
    today = date.today()
    invoices = invoice_list(db, user_id)
    all_customers = customer_list(db, user_id)
    financial_data = analytics(db, user_id)
    chart = financial_data["months"]
    revenue = sum(cents(item["revenue"]) for item in chart)
    expenses = sum(cents(item["expenses"]) for item in chart)
    recent_rev = sum(cents(item["revenue"]) for item in chart[-3:])
    prior_rev = sum(cents(item["revenue"]) for item in chart[:3])
    recent_exp = sum(cents(item["expenses"]) for item in chart[-3:])
    prior_exp = sum(cents(item["expenses"]) for item in chart[:3])
    period_start = shift_month(month_start(today), -5).isoformat()
    period_end = shift_month(month_start(today), 1).isoformat()
    overdue = [item for item in invoices if item["status"] == "overdue"]
    due_soon = [item for item in invoices if item["status"] == "sent"
                and today.isoformat() <= item["due_date"] <= (today + timedelta(days=30)).isoformat()]
    category_expenses = db.execute(
        """SELECT category,SUM(amount) AS total FROM expenses
           WHERE user_id=? AND expense_date>=? AND expense_date<?
           GROUP BY category ORDER BY total DESC LIMIT 4""",
        (user_id, period_start, period_end)).fetchall()
    service_rows = db.execute(
        """SELECT i.service_category,COALESCE(SUM(p.amount),0) AS collected
           FROM invoices i LEFT JOIN payments p
           ON p.invoice_id=i.id AND p.user_id=i.user_id AND p.paid_at>=? AND p.paid_at<?
           WHERE i.user_id=? GROUP BY i.service_category ORDER BY collected DESC LIMIT 5""",
        (period_start, period_end, user_id)).fetchall()
    tagged_cost_rows = db.execute(
        """SELECT service_category,SUM(amount) AS total FROM expenses
           WHERE user_id=? AND expense_date>=? AND expense_date<? AND service_category<>''
           GROUP BY service_category""", (user_id, period_start, period_end)).fetchall()
    tagged_costs = {row["service_category"]: cents(row["total"]) for row in tagged_cost_rows}
    service_revenue = [row for row in service_rows if cents(row["collected"])]
    service_contribution = []
    for row in service_revenue:
        collected = cents(row["collected"])
        direct_costs = tagged_costs.get(row["service_category"], 0)
        service_contribution.append({
            "category": row["service_category"],
            "collected": amount(collected),
            "tagged_direct_costs": amount(direct_costs),
            "contribution_before_shared_costs": amount(collected - direct_costs),
            "margin_before_shared_costs_percent": round(
                (collected - direct_costs) / collected * 100, 1
            ),
        })
    outstanding = sum(cents(item["balance"]) for item in invoices if item["status"] != "draft")
    balance = cents(recent_rev - recent_exp)
    performance = [
        f"Collected {settings['currency']} {amount(revenue):,.2f} over the last six months.",
        f"Expenses were {settings['currency']} {amount(expenses):,.2f}; net cash flow was {settings['currency']} {amount(revenue-expenses):,.2f}.",
        growth_description("Collected revenue", recent_rev, prior_rev),
        growth_description("Expenses", recent_exp, prior_exp),
        (f"Monthly profit shifted from {settings['currency']} {chart[-2]['net']:,.2f} "
         f"to {settings['currency']} {chart[-1]['net']:,.2f} in the latest month."
         if len(chart) > 1 else "Profit and loss trends are shown month by month."),
    ]
    warnings = []
    if recent_rev < prior_rev and prior_rev:
        warnings.append("Collected revenue is trending down compared with the previous three months.")
    if recent_exp > prior_exp and prior_exp:
        warnings.append("Expenses are increasing compared with the previous three months.")
    if overdue:
        warnings.append(f"{len(overdue)} overdue invoice(s) total {settings['currency']} "
                        f"{amount(sum(cents(i['balance']) for i in overdue)):,.2f}.")
    if outstanding:
        warnings.append(f"{settings['currency']} {amount(outstanding):,.2f} is outstanding across sent invoices.")
    if balance < 0:
        warnings.append("Cash flow over the latest three months is negative.")
    if financial_data["low_cash_balance"]:
        warnings.append(
            f"Estimated cash is {settings['currency']} {financial_data['estimated_cash_balance']:,.2f}, "
            f"below one month of recorded expenses "
            f"({settings['currency']} {financial_data['average_monthly_expenses']:,.2f})."
        )
    if not warnings:
        warnings.append("No overdue invoices or negative three-month cash flow signals detected.")
    opportunities = []
    leaders = sorted(
        (item for item in all_customers if cents(item["collected"]) > 0),
        key=lambda item: cents(item["collected"]), reverse=True,
    )[:3]
    if leaders:
        opportunities.append("Highest-collected customers: " + ", ".join(
            f"{item['name']} ({settings['currency']} {item['collected']:,.2f})" for item in leaders) + ".")
    else:
        opportunities.append("Record invoice payments to identify your highest-revenue customers.")
    if category_expenses:
        opportunities.append("Largest expense categories: " + ", ".join(
            f"{row['category']} ({settings['currency']} {row['total']:,.2f})"
            for row in category_expenses) + ". Review these for savings.")
    if service_revenue:
        opportunities.append("Top service categories by collected revenue: " + ", ".join(
            f"{row['service_category']} ({settings['currency']} {row['collected']:,.2f})"
            for row in service_revenue) + ".")
    if service_contribution:
        leaders = sorted(
            (row for row in service_contribution
             if cents(row["contribution_before_shared_costs"]) > 0),
            key=lambda row: cents(row["contribution_before_shared_costs"]), reverse=True,
        )
        if leaders:
            opportunities.append("Strongest service-line contribution after tagged direct costs "
                                 "(before shared costs): " + ", ".join(
                f"{row['category']} ({settings['currency']} "
                f"{row['contribution_before_shared_costs']:,.2f}, "
                f"{row['margin_before_shared_costs_percent']:.1f}% contribution margin)"
                for row in leaders[:3]) + ".")
        elif any(row["tagged_direct_costs"] for row in service_contribution):
            warnings.append("Tagged direct costs exceed collected revenue for the measured service lines.")
    elif service_revenue:
        opportunities.append("Tag matching expenses with each service category to measure service-line "
                             "contribution after direct costs.")
    if due_soon:
        opportunities.append(f"{len(due_soon)} invoice(s) totaling "
                             f"{settings['currency']} {amount(sum(cents(i['balance']) for i in due_soon)):,.2f} "
                             "are due in the next 30 days.")
    return {
        "currency": settings["currency"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "financial_summary": {
            "currency": settings["currency"], "period": "latest 6 months",
            "monthly_cash_flow": chart,
            "estimated_cash_balance": financial_data["estimated_cash_balance"],
            "average_monthly_expenses": financial_data["average_monthly_expenses"],
            "low_cash_balance": financial_data["low_cash_balance"],
            "revenue_growth_percent": growth(recent_rev, prior_rev),
            "expense_growth_percent": growth(recent_exp, prior_exp),
            "net_cash_flow_latest_3_months": amount(balance),
            "outstanding_invoices": amount(outstanding),
            "overdue_invoice_count": len(overdue),
            "overdue_invoice_balance": amount(sum(cents(i["balance"]) for i in overdue)),
            "upcoming_30_day_collections": amount(sum(cents(i["balance"]) for i in due_soon)),
            "expense_categories": [{"category": row["category"], "amount": amount(cents(row["total"]))}
                                   for row in category_expenses],
            "service_revenue": [{"category": row["service_category"],
                                 "collected": amount(cents(row["collected"]))}
                                for row in service_rows if cents(row["collected"])],
            "service_contribution_before_shared_costs": service_contribution,
        },
        "performance": performance, "warnings": warnings, "opportunities": opportunities,
        "outlook": ("Net cash flow is positive over the latest three months." if balance >= 0
                    else "Net cash flow is negative over the latest three months; prioritize collections and review spending."),
    }


def main():
    env_file = ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            item = line.strip()
            if not item or item.startswith("#") or "=" not in item:
                continue
            name, _, value = item.partition("=")
            name = name.strip()
            value = value.strip().strip("\"'")
            if name and name not in os.environ:
                os.environ[name] = value
    has_supabase_url = bool(os.environ.get("SUPABASE_URL"))
    has_supabase_key = bool(os.environ.get("SUPABASE_ANON_KEY"))
    if has_supabase_url != has_supabase_key:
        raise RuntimeError("Set both SUPABASE_URL and SUPABASE_ANON_KEY, or leave both unset.")
    if has_supabase_url:
        from supabase_app import SupabaseAppHandler
        handler = SupabaseAppHandler
        logging.info("Using Supabase Auth and Postgres (publishable key; row-level security enabled).")
    else:
        initialize_database()
        handler = AppHandler
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    logging.info("Smart Invoice AI running at http://127.0.0.1:%s", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Shutting down Smart Invoice AI")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
