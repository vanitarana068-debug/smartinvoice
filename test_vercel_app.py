import io
import json
import unittest
from unittest.mock import patch

import api.index as vercel_app


class VercelAdapterTests(unittest.TestCase):
    def invoke(self, path, method="GET", body=b"", headers=None, query=""):
        captured = {}
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "CONTENT_LENGTH": str(len(body)) if body else "",
            "CONTENT_TYPE": "application/json" if body else "",
            "wsgi.input": io.BytesIO(body),
            "REMOTE_ADDR": "127.0.0.1",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8000",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.errors": io.StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": True,
            "wsgi.run_once": True,
        }
        environ.update(headers or {})
        response_body = b"".join(vercel_app.application(
            environ, lambda status, response_headers: captured.update(
                status=status, headers=response_headers,
            )
        ))
        return captured, response_body

    def test_api_health_route_through_vercel_rewrite(self):
        with patch.object(vercel_app, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(vercel_app, "SUPABASE_ANON_KEY", "sb_publishable_test"):
            result, body = self.invoke("/api/index", query="__path=%2Fapi%2Fhealth")

        self.assertEqual(result["status"], "200 OK")
        self.assertEqual(json.loads(body), {"ok": True, "database": "supabase"})

    def test_serves_frontend_html_through_vercel_function(self):
        with patch.object(vercel_app, "SUPABASE_URL", "https://example.supabase.co"), \
             patch.object(vercel_app, "SUPABASE_ANON_KEY", "sb_publishable_test"):
            result, body = self.invoke("/", query="__path=%2F")

        self.assertEqual(result["status"], "200 OK")
        self.assertIn(b"Smart Invoice AI", body)
        self.assertIn(("Content-Type", "text/html; charset=utf-8"), result["headers"])

    def test_rejects_missing_supabase_environment_before_dispatch(self):
        with patch.object(vercel_app, "SUPABASE_URL", ""), \
             patch.object(vercel_app, "SUPABASE_ANON_KEY", ""):
            result, body = self.invoke("/api/index", query="__path=%2Fapi%2Fhealth")

        self.assertEqual(result["status"], "503 Service Unavailable")
        self.assertIn(b"SUPABASE_URL", body)


if __name__ == "__main__":
    unittest.main()
