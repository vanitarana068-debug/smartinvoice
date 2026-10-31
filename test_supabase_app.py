import json
import unittest
from unittest.mock import patch

import server
import supabase_app


class SupabaseIntegrationTests(unittest.TestCase):
    def test_requests_use_publishable_key_and_signed_in_user_token(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return None

            def read(self, _limit):
                return b"[]"

        with patch.object(supabase_app, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(supabase_app, "SUPABASE_ANON_KEY", "sb_publishable_test"), \
             patch("urllib.request.urlopen", return_value=Response()) as urlopen:
            result = supabase_app.supabase_request("/rest/v1/customers", token="user-access-token")

        self.assertEqual(result, [])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Apikey"), "sb_publishable_test")
        self.assertEqual(request.get_header("Authorization"), "Bearer user-access-token")
        self.assertNotIn("service_role", json.dumps(request.headers))

    def test_finance_snapshot_reuses_cash_basis_calculations(self):
        user_id = "11111111-1111-4111-8111-111111111111"
        today = server.date.today().isoformat()
        records = {
            "settings": [{
                "user_id": user_id, "business_name": "Northstar", "currency": "USD",
                "opening_cash_balance": None, "opening_balance_date": today,
            }],
            "customers": [{
                "id": 12, "user_id": user_id, "name": "Northstar Studio",
                "email": "", "company": "", "created_at": today,
            }],
            "invoices": [{
                "id": 40, "user_id": user_id, "customer_id": 12, "number": "INV-2026-0040",
                "description": "Strategy", "amount": 100, "issue_date": today, "due_date": today,
                "status": "sent", "created_at": today, "service_category": "Consulting",
            }],
            "expenses": [],
            "payments": [{
                "id": 75, "user_id": user_id, "invoice_id": 40, "amount": 40,
                "paid_at": today, "method": "Transfer", "created_at": today,
            }],
            "reminders": [],
        }
        with patch.object(supabase_app, "rest_rows", side_effect=lambda table, *_args, **_kwargs: records[table]):
            with supabase_app.finance_database(user_id, "test-token") as db:
                invoices = server.invoice_list(db, 1)
                self.assertEqual(invoices[0]["balance"], 60)
                self.assertEqual(invoices[0]["customer_name"], "Northstar Studio")
                self.assertEqual(server.dashboard(db, 1)["revenue"], 40)


if __name__ == "__main__":
    unittest.main()
