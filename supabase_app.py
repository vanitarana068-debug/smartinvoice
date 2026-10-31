import json
import logging
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import date
from http.cookies import CookieError, SimpleCookie

import server as core


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
ACCESS_COOKIE = "smart_invoice_access"
REFRESH_COOKIE = "smart_invoice_refresh"


class SupabaseError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


def supabase_request(path, method="GET", token=None, body=None, prefer=None):
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body, separators=(",", ":")).encode() if body is not None else None
    request = urllib.request.Request(
        SUPABASE_URL + path, data=data, headers=headers, method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read(2_000_000)
            return json.loads(payload) if payload else None
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read(1_000_000))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}
        message = payload.get("msg") or payload.get("message") or payload.get("error_description")
        status = error.code
        if status == 401:
            message = "Your session has expired. Please sign in again."
        elif status == 409:
            message = "This record conflicts with existing business records."
        elif payload.get("code") in ("42P01", "PGRST205") or (
            status == 404 and ("schema cache" in str(message).lower() or "relation" in str(message).lower())
        ):
            status = 503
            message = "Supabase tables are missing. Run supabase/schema.sql in your project's SQL Editor."
        elif status >= 500 or not message:
            message = "Supabase could not complete the request. Please try again."
        raise SupabaseError(status, message)
    except (urllib.error.URLError, TimeoutError) as error:
        logging.warning("Supabase request failed: %s", error)
        raise SupabaseError(502, "Could not connect to Supabase. Check your connection and project settings.")


def rest_rows(table, user_id, token, order=None):
    query = {"select": "*", "user_id": f"eq.{user_id}"}
    if order:
        query["order"] = order
    path = "/rest/v1/" + table + "?" + urllib.parse.urlencode(query)
    return supabase_request(path, token=token) or []


@contextmanager
def finance_database(user_id, token):
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE settings (
            user_id INTEGER PRIMARY KEY, business_name TEXT NOT NULL DEFAULT '',
            currency TEXT NOT NULL DEFAULT 'USD', opening_cash_balance REAL,
            opening_balance_date TEXT NOT NULL DEFAULT '1970-01-01'
        );
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, name TEXT NOT NULL,
            email TEXT NOT NULL DEFAULT '', company TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE invoices (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, customer_id INTEGER NOT NULL,
            number TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', amount REAL NOT NULL,
            issue_date TEXT NOT NULL, due_date TEXT NOT NULL, status TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            service_category TEXT NOT NULL DEFAULT 'General services'
        );
        CREATE TABLE expenses (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, category TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '', amount REAL NOT NULL, expense_date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, service_category TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE payments (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, invoice_id INTEGER NOT NULL,
            amount REAL NOT NULL, paid_at TEXT NOT NULL, method TEXT NOT NULL DEFAULT 'Bank transfer',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE reminders (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, invoice_id INTEGER NOT NULL,
            sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    records = {
        "settings": rest_rows("settings", user_id, token),
        "customers": rest_rows("customers", user_id, token, "name.asc"),
        "invoices": rest_rows("invoices", user_id, token, "issue_date.desc"),
        "expenses": rest_rows("expenses", user_id, token, "expense_date.desc"),
        "payments": rest_rows("payments", user_id, token, "paid_at.desc"),
        "reminders": rest_rows("reminders", user_id, token, "sent_at.desc"),
    }
    for row in records["settings"]:
        db.execute(
            """INSERT INTO settings(user_id,business_name,currency,opening_cash_balance,opening_balance_date)
               VALUES(1,?,?,?,?)""",
            (row["business_name"], row["currency"], row.get("opening_cash_balance"),
             row.get("opening_balance_date", "1970-01-01")),
        )
    for table in ("customers", "invoices", "expenses", "payments", "reminders"):
        columns = [row[1] for row in db.execute(f"PRAGMA table_info({table})")]
        for row in records[table]:
            values = [1 if column == "user_id" else row.get(column) for column in columns]
            db.execute(
                f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                values,
            )
    try:
        yield db
    finally:
        db.close()


class SupabaseAppHandler(core.AppHandler):
    def __init__(self, *args, **kwargs):
        self._pending_cookies = []
        super().__init__(*args, **kwargs)

    def end_headers(self):
        for cookie in self._pending_cookies:
            self.send_header("Set-Cookie", cookie)
        self._pending_cookies.clear()
        super().end_headers()

    def request_cookies(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
        except (CookieError, ValueError):
            raise core.APIError(401, "Please sign in to continue.")
        return cookies

    def token(self, cookie_name):
        item = self.request_cookies().get(cookie_name)
        return item.value if item else None

    def set_session(self, session):
        access = session.get("access_token")
        refresh = session.get("refresh_token")
        if not access or not refresh:
            raise core.APIError(502, "Supabase did not return a sign-in session.")
        secure = "; Secure" if os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "yes") else ""
        access_age = max(60, min(int(session.get("expires_in", 3600)), 86400))
        self._pending_cookies.extend((
            f"{ACCESS_COOKIE}={access}; Path=/; HttpOnly; SameSite=Lax; Max-Age={access_age}{secure}",
            f"{REFRESH_COOKIE}={refresh}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000{secure}",
        ))

    def clear_session(self):
        secure = "; Secure" if os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "yes") else ""
        self._pending_cookies.extend((
            f"{ACCESS_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0{secure}",
            f"{REFRESH_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0{secure}",
        ))

    def current_user(self):
        access = self.token(ACCESS_COOKIE)
        if not access:
            raise core.APIError(401, "Please sign in to continue.")
        try:
            user = supabase_request("/auth/v1/user", token=access)
        except SupabaseError as error:
            refresh = self.token(REFRESH_COOKIE)
            if error.status != 401 or not refresh:
                raise core.APIError(401, "Your session has expired. Please sign in again.")
            session = supabase_request(
                "/auth/v1/token?grant_type=refresh_token", "POST",
                body={"refresh_token": refresh},
            )
            self.set_session(session)
            access = session["access_token"]
            user = session.get("user") or supabase_request(
                "/auth/v1/user", token=access,
            )
        metadata = user.get("user_metadata") or {}
        return {
            "id": user["id"],
            "email": user.get("email", ""),
            "name": metadata.get("full_name") or user.get("email", "").split("@")[0],
        }, access

    def auth_success(self, session):
        user = session.get("user") or {}
        metadata = user.get("user_metadata") or {}
        if not session.get("access_token"):
            raise core.APIError(
                202,
                "Check your email to confirm your account, then return here to sign in.",
            )
        self.set_session(session)
        user_info = {
            "id": user.get("id"),
            "email": user.get("email", ""),
            "name": metadata.get("full_name") or user.get("email", "").split("@")[0],
        }
        self.ensure_settings(user_info["id"], session["access_token"], user_info["name"])
        with finance_database(user_info["id"], session["access_token"]) as db:
            settings = core.user_settings(db, 1)
        self.send_json(200, {"user": user_info, "settings": settings})

    @staticmethod
    def ensure_settings(user_id, token, name):
        supabase_request(
            "/rest/v1/settings?on_conflict=user_id", "POST", token,
            {"user_id": user_id, "business_name": f"{name}'s business", "currency": "USD"},
            "resolution=ignore-duplicates,return=minimal",
        )

    def do_GET(self):
        parsed = core.urlparse(self.path)
        if parsed.path == "/" or parsed.path in ("/app.js", "/styles.css"):
            return self.static_file("index.html" if parsed.path == "/" else parsed.path.lstrip("/"))
        if not parsed.path.startswith("/api/"):
            return self.send_json(404, {"error": "Not found."})
        if parsed.path == "/api/health":
            return self.send_json(200, {"ok": True, "database": "supabase"})
        try:
            user, token = self.current_user()
            if parsed.path == "/api/me":
                with finance_database(user["id"], token) as db:
                    self.send_json(200, {
                        "user": user, "settings": core.user_settings(db, 1),
                        "aiAvailable": bool(os.environ.get("GEMINI_API_KEY")),
                    })
            else:
                with finance_database(user["id"], token) as db:
                    routes = {
                        "/api/dashboard": lambda: self.send_json(200, core.dashboard(db, 1)),
                        "/api/invoices": lambda: self.send_json(200, {"invoices": core.invoice_list(db, 1)}),
                        "/api/customers": lambda: self.send_json(200, {"customers": core.customer_list(db, 1)}),
                        "/api/expenses": lambda: self.send_json(200, {"expenses": core.expense_list(db, 1)}),
                        "/api/payments": lambda: self.send_json(200, {"payments": core.payment_list(db, 1)}),
                        "/api/analytics": lambda: self.send_json(200, core.analytics(db, 1)),
                        "/api/reminders": lambda: self.send_json(200, {"reminders": core.reminder_list(db, 1)}),
                        "/api/settings": lambda: self.send_json(200, {"settings": core.user_settings(db, 1)}),
                        "/api/insights": lambda: self.send_json(200, {
                            "insights": core.local_insights(db, 1),
                            "aiAvailable": bool(os.environ.get("GEMINI_API_KEY")),
                        }),
                        "/api/reports.csv": lambda: core.AppHandler.send_report(self, db, 1),
                    }
                    handler = routes.get(parsed.path)
                    if handler:
                        handler()
                    else:
                        self.send_json(404, {"error": "Not found."})
        except core.APIError as error:
            self.fail(error)
        except SupabaseError as error:
            self.fail(core.APIError(error.status if error.status < 500 else 502, error.message))
        except (sqlite3.Error, KeyError, TypeError, ValueError):
            logging.exception("Supabase-backed request failed for %s", parsed.path)
            self.send_json(500, {"error": "Could not load your financial records. Please try again."})

    def do_POST(self):
        parsed = core.urlparse(self.path)
        try:
            data = self.read_json()
            if parsed.path == "/api/register":
                name = core.clean_text(data.get("name"), "Name", 80)
                email = core.clean_email(data.get("email"))
                password = data.get("password")
                if not isinstance(password, str) or not 8 <= len(password) <= 256:
                    raise core.APIError(400, "Password must be between 8 and 256 characters.")
                session = supabase_request(
                    "/auth/v1/signup", "POST",
                    body={"email": email, "password": password, "data": {"full_name": name}},
                )
                return self.auth_success(session)
            if parsed.path == "/api/login":
                email = core.clean_email(data.get("email"))
                password = data.get("password")
                if not isinstance(password, str) or len(password) > 256:
                    raise core.APIError(401, "Email or password is incorrect.")
                session = supabase_request(
                    "/auth/v1/token?grant_type=password", "POST",
                    body={"email": email, "password": password},
                )
                return self.auth_success(session)
            if parsed.path == "/api/logout":
                access = self.token(ACCESS_COOKIE)
                if access:
                    try:
                        supabase_request("/auth/v1/logout", "POST", access)
                    except SupabaseError as error:
                        if error.status != 401:
                            raise
                self.clear_session()
                self.send_response(204)
                self.end_headers()
                return

            user, token = self.current_user()
            user_id = user["id"]
            if parsed.path == "/api/insights/gemini":
                with finance_database(user_id, token) as db:
                    return core.AppHandler.generate_gemini_insights(self, db, 1)
            with finance_database(user_id, token) as db:
                if parsed.path == "/api/customers":
                    row = {
                        "user_id": user_id,
                        "name": core.clean_text(data.get("name"), "Customer name", 120),
                        "email": core.clean_email(data.get("email"), required=False),
                        "company": core.clean_text(data.get("company", ""), "Company", 120, required=False),
                    }
                    created = self.insert_row("customers", row, token)
                    return self.send_json(201, {"id": created["id"]})
                if parsed.path == "/api/invoices":
                    customer_id = core.parse_id(data.get("customer_id"))
                    if not db.execute("SELECT 1 FROM customers WHERE id=?", (customer_id,)).fetchone():
                        raise core.APIError(400, "Choose one of your customers.")
                    total = core.money_to_cents(data.get("amount"))
                    issue = core.valid_date(data.get("issue_date", date.today().isoformat()), "Issue date")
                    due = core.valid_date(data.get("due_date"), "due date")
                    if due < issue:
                        raise core.APIError(400, "The due date cannot be before the issue date.")
                    number = core.clean_text(data.get("number"), "Invoice number", 40) if data.get("number") else (
                        f"INV-{issue.year}-{(db.execute('SELECT COALESCE(MAX(id),0)+1 FROM invoices').fetchone()[0]):04d}"
                    )
                    status = data.get("status", "sent")
                    if status not in ("draft", "sent"):
                        raise core.APIError(400, "New invoices must be drafts or sent.")
                    row = {
                        "user_id": user_id, "customer_id": customer_id, "number": number,
                        "description": core.clean_text(data.get("description", ""), "Description", 500, required=False),
                        "amount": core.amount(total), "issue_date": issue.isoformat(),
                        "due_date": due.isoformat(), "status": status,
                        "service_category": core.clean_text(
                            data.get("service_category", "General services"),
                            "Service category", 80, required=False,
                        ) or "General services",
                    }
                    created = self.insert_row("invoices", row, token)
                    return self.send_json(201, {"id": created["id"], "number": number})
                if parsed.path == "/api/expenses":
                    expense_date = core.valid_date(data.get("expense_date", date.today().isoformat()), "expense date")
                    if expense_date > date.today():
                        raise core.APIError(400, "An expense date cannot be in the future.")
                    row = {
                        "user_id": user_id, "category": core.clean_text(data.get("category"), "Category", 80),
                        "description": core.clean_text(data.get("description", ""), "Description", 500, required=False),
                        "amount": core.amount(core.money_to_cents(data.get("amount"))),
                        "expense_date": expense_date.isoformat(),
                        "service_category": core.clean_text(
                            data.get("service_category", ""), "Service category", 80, required=False,
                        ),
                    }
                    created = self.insert_row("expenses", row, token)
                    return self.send_json(201, {"id": created["id"]})
                if parsed.path == "/api/payments":
                    invoice_id = core.parse_id(data.get("invoice_id"))
                    invoice = db.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
                    if not invoice:
                        raise core.APIError(404, "Invoice not found.")
                    if invoice["status"] == "draft":
                        raise core.APIError(400, "Send the draft invoice before recording a payment.")
                    paid = db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?",
                                      (invoice_id,)).fetchone()[0]
                    remaining = core.cents(invoice["amount"]) - core.cents(paid)
                    total = core.money_to_cents(data.get("amount"))
                    if total > remaining:
                        raise core.APIError(400, f"Payment exceeds the remaining balance of {core.amount(remaining):.2f}.")
                    paid_at = core.valid_date(data.get("paid_at", date.today().isoformat()), "payment date")
                    if paid_at > date.today():
                        raise core.APIError(400, "A payment date cannot be in the future.")
                    created = self.insert_row("payments", {
                        "user_id": user_id, "invoice_id": invoice_id, "amount": core.amount(total),
                        "paid_at": paid_at.isoformat(),
                        "method": core.clean_text(data.get("method", "Bank transfer"), "Payment method", 60),
                    }, token)
                    return self.send_json(201, {
                        "id": created["id"], "invoice_id": invoice_id,
                        "remaining": core.amount(remaining - total),
                    })
                if parsed.path == "/api/reminders":
                    invoice_id = core.parse_id(data.get("invoice_id"))
                    invoice = db.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
                    if not invoice:
                        raise core.APIError(404, "Invoice not found.")
                    paid = db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?",
                                      (invoice_id,)).fetchone()[0]
                    if invoice["status"] == "draft" or core.cents(paid) >= core.cents(invoice["amount"]):
                        raise core.APIError(400, "Only sent invoices with a balance need payment reminders.")
                    self.insert_row("reminders", {"user_id": user_id, "invoice_id": invoice_id}, token)
                    return self.send_json(201, {"ok": True})
                self.send_json(404, {"error": "Not found."})
        except core.APIError as error:
            self.fail(error)
        except SupabaseError as error:
            if error.status == 409:
                message = "That invoice number is already in use." if parsed.path == "/api/invoices" else error.message
                return self.fail(core.APIError(409, message))
            self.fail(core.APIError(error.status if error.status < 500 else 502, error.message))
        except (sqlite3.Error, KeyError, TypeError, ValueError):
            logging.exception("Supabase-backed request failed for %s", parsed.path)
            self.send_json(500, {"error": "Could not save your record. Please try again."})

    def insert_row(self, table, row, token):
        result = supabase_request(
            f"/rest/v1/{table}", "POST", token, row, "return=representation",
        )
        if not result:
            raise core.APIError(502, "Supabase did not confirm the saved record.")
        return result[0]

    def do_PATCH(self):
        parsed = core.urlparse(self.path)
        try:
            data = self.read_json()
            user, token = self.current_user()
            user_id = user["id"]
            if parsed.path == "/api/settings":
                business_name = core.clean_text(data.get("business_name"), "Business name", 120)
                currency = str(data.get("currency", "")).upper()
                if not core.CURRENCY_RE.fullmatch(currency):
                    raise core.APIError(400, "Choose a valid three-letter currency code.")
                with finance_database(user_id, token) as db:
                    current = core.user_settings(db, 1)
                raw_balance = data.get("opening_cash_balance", current["opening_cash_balance"])
                opening_balance = None if raw_balance is None or raw_balance == "" else core.amount(
                    core.signed_money_to_cents(raw_balance)
                )
                opening_date = core.valid_date(
                    data.get("opening_balance_date", current["opening_balance_date"]),
                    "opening balance date",
                )
                if opening_date > date.today():
                    raise core.APIError(400, "The opening balance date cannot be in the future.")
                supabase_request(
                    "/rest/v1/settings?on_conflict=user_id", "POST", token,
                    {"user_id": user_id, "business_name": business_name, "currency": currency,
                     "opening_cash_balance": opening_balance, "opening_balance_date": opening_date.isoformat()},
                    "resolution=merge-duplicates,return=minimal",
                )
                with finance_database(user_id, token) as db:
                    return self.send_json(200, {"settings": core.user_settings(db, 1)})
            raw_id = parsed.path.rsplit("/", 1)[-1]
            row_id = core.parse_id(raw_id)
            if parsed.path.startswith("/api/customers/"):
                patch = {
                    "name": core.clean_text(data.get("name"), "Customer name", 120),
                    "email": core.clean_email(data.get("email"), required=False),
                    "company": core.clean_text(data.get("company", ""), "Company", 120, required=False),
                }
                self.patch_row("customers", row_id, user_id, token, patch, "Customer not found.")
                return self.send_json(200, {"ok": True})
            if parsed.path.startswith("/api/invoices/"):
                if data.get("status") != "sent":
                    raise core.APIError(400, "A draft invoice can only be marked as sent.")
                result = self.patch_row(
                    "invoices", row_id, user_id, token, {"status": "sent"},
                    "Invoice not found.", only_draft=True,
                )
                if not result:
                    raise core.APIError(409, "Only draft invoices can be marked as sent.")
                return self.send_json(200, {"ok": True})
            self.send_json(404, {"error": "Not found."})
        except core.APIError as error:
            self.fail(error)
        except SupabaseError as error:
            self.fail(core.APIError(error.status if error.status < 500 else 502, error.message))
        except (sqlite3.Error, KeyError, TypeError, ValueError):
            logging.exception("Supabase-backed request failed for %s", parsed.path)
            self.send_json(500, {"error": "Could not update your record. Please try again."})

    def patch_row(self, table, row_id, user_id, token, patch, not_found, only_draft=False):
        query = {"id": f"eq.{row_id}", "user_id": f"eq.{user_id}", "select": "id"}
        if only_draft:
            query["status"] = "eq.draft"
        result = supabase_request(
            f"/rest/v1/{table}?" + urllib.parse.urlencode(query), "PATCH", token,
            patch, "return=representation",
        )
        if not result and not only_draft:
            raise core.APIError(404, not_found)
        if not result and only_draft:
            exists = supabase_request(
                f"/rest/v1/{table}?" + urllib.parse.urlencode({
                    "id": f"eq.{row_id}", "user_id": f"eq.{user_id}", "select": "id",
                }), token=token,
            )
            if not exists:
                raise core.APIError(404, not_found)
        return result

    def do_DELETE(self):
        parsed = core.urlparse(self.path)
        try:
            user, token = self.current_user()
            table = None
            row_id = core.parse_id(parsed.path.rsplit("/", 1)[-1])
            if parsed.path.startswith("/api/customers/"):
                table = "customers"
            elif parsed.path.startswith("/api/expenses/"):
                table = "expenses"
            elif parsed.path.startswith("/api/invoices/"):
                table = "invoices"
            if not table:
                return self.send_json(404, {"error": "Not found."})
            query = {"id": f"eq.{row_id}", "user_id": f"eq.{user['id']}", "select": "id"}
            if table == "invoices":
                query["status"] = "eq.draft"
                with finance_database(user["id"], token) as db:
                    has_payments = db.execute(
                        "SELECT 1 FROM payments WHERE invoice_id=? LIMIT 1", (row_id,),
                    ).fetchone()
                if has_payments:
                    raise core.APIError(409, "Only draft invoices without payments can be deleted.")
            deleted = supabase_request(
                f"/rest/v1/{table}?" + urllib.parse.urlencode(query), "DELETE", token,
                prefer="return=representation",
            )
            if not deleted:
                if table == "invoices":
                    raise core.APIError(409, "Only draft invoices without payments can be deleted.")
                raise core.APIError(404, "Record not found.")
            return self.send_json(200, {"ok": True})
        except core.APIError as error:
            self.fail(error)
        except SupabaseError as error:
            message = "This customer has invoices and cannot be deleted." if error.status == 409 else error.message
            self.fail(core.APIError(error.status if error.status < 500 else 502, message))
        except (sqlite3.Error, KeyError, TypeError, ValueError):
            logging.exception("Supabase-backed request failed for %s", parsed.path)
            self.send_json(500, {"error": "Could not delete the record. Please try again."})
