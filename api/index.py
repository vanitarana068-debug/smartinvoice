import io
import os
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_local_environment():
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if not item or item.startswith("#") or "=" not in item:
            continue
        name, _, value = item.partition("=")
        name = name.strip()
        value = value.strip().strip("\"'")
        if name and name not in os.environ:
            os.environ[name] = value


load_local_environment()

from supabase_app import SUPABASE_ANON_KEY, SUPABASE_URL, SupabaseAppHandler


class _OpenBytesIO(io.BytesIO):
    def close(self):
        self.flush()


class _RequestSocket:
    def __init__(self, request_data):
        self._request = _OpenBytesIO(request_data)
        self.response = _OpenBytesIO()

    def settimeout(self, _timeout):
        return None

    def makefile(self, mode, *_args, **_kwargs):
        return self._request if "r" in mode else self.response

    def sendall(self, data):
        self.response.write(data)

    def close(self):
        return None


class _Server:
    server_version = "SmartInvoiceVercel/1.0"
    sys_version = ""


def _handler_request(environ):
    query = parse_qsl(environ.get("QUERY_STRING", ""), keep_blank_values=True)
    route_path = None
    forwarded_query = []
    for key, value in query:
        if key == "__path" and route_path is None:
            route_path = value
        else:
            forwarded_query.append((key, value))
    path = route_path or environ.get("PATH_INFO", "/")
    if not path.startswith("/") or "\r" in path or "\n" in path:
        path = "/"
    query_string = urlencode(forwarded_query, doseq=True)
    request_target = path + (f"?{query_string}" if query_string else "")
    method = environ.get("REQUEST_METHOD", "GET").upper()
    request = [f"{method} {request_target} HTTP/1.0\r\n"]
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            header_name = key[5:].replace("_", "-").title()
            request.append(f"{header_name}: {value}\r\n")
    if environ.get("CONTENT_TYPE"):
        request.append(f"Content-Type: {environ['CONTENT_TYPE']}\r\n")
    if environ.get("CONTENT_LENGTH"):
        request.append(f"Content-Length: {environ['CONTENT_LENGTH']}\r\n")
    request.append("Connection: close\r\n\r\n")
    body = environ.get("wsgi.input", io.BytesIO()).read()
    return "".join(request).encode("latin-1") + body


def application(environ, start_response):
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        body = b'{"error":"Set SUPABASE_URL and SUPABASE_ANON_KEY in Vercel project settings."}'
        start_response("503 Service Unavailable", [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ])
        return [body]

    request_socket = _RequestSocket(_handler_request(environ))
    handler = SupabaseAppHandler(
        request_socket,
        (environ.get("REMOTE_ADDR", "127.0.0.1"), 0),
        _Server(),
    )
    response = request_socket.response.getvalue()
    header_end = response.find(b"\r\n\r\n")
    if header_end < 0:
        body = b'{"error":"The request could not be completed."}'
        start_response("500 Internal Server Error", [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ])
        return [body]

    status_line, raw_headers = response[:header_end].split(b"\r\n", 1)
    try:
        status = status_line.decode("latin-1").split(" ", 2)
        status_code = int(status[1])
        reason = status[2] if len(status) > 2 else "Unknown"
        headers = [
            (name.decode("latin-1"), value.decode("latin-1").strip())
            for name, value in (
                line.split(b":", 1) for line in raw_headers.split(b"\r\n") if b":" in line
            )
        ]
    except (ValueError, UnicodeDecodeError):
        body = b'{"error":"The request could not be completed."}'
        start_response("500 Internal Server Error", [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ])
        return [body]

    start_response(f"{status_code} {reason}", headers)
    return [response[header_end + 4:]]


app = application
