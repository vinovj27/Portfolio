from __future__ import annotations

import json
import re
import threading
import time
from collections import defaultdict, deque
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from urllib.parse import unquote, urlparse

from . import ics, schedule
from .store import ApiError, Store

COOKIE = "petrem_session"
MAX_BODY = 64 * 1024
LOGIN_WINDOW = 15 * 60
LOGIN_ATTEMPTS = 8
STATIC_TYPES = {
    ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml", ".png": "image/png", ".json": "application/json",
}
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
       "base-uri 'none'; form-action 'self'")
DEMO_EMAIL = "demo@petrem.app"


class Request:
    def __init__(self, handler: BaseHTTPRequestHandler, app: "App") -> None:
        self.handler = handler
        self.app = app
        self.method = handler.command
        self.path = urlparse(handler.path).path
        jar = cookies.SimpleCookie(handler.headers.get("Cookie", ""))
        self.token = jar[COOKIE].value if COOKIE in jar else None
        self._user = ...
        self.set_cookie: str | None = None

    @property
    def user(self) -> dict | None:
        if self._user is ...:
            self._user = self.app.store.user_for_session(self.token)
        return self._user

    def body(self) -> dict:
        length = int(self.handler.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ApiError(413, "Request body is too large.")
        if not length:
            return {}
        if "application/json" not in (self.handler.headers.get("Content-Type") or ""):
            raise ApiError(415, "Send the request body as JSON.")
        try:
            data = json.loads(self.handler.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ApiError(400, "Request body is not valid JSON.") from None
        if not isinstance(data, dict):
            raise ApiError(400, "Expected a JSON object.")
        return data


class App:
    def __init__(self, store: Store, demo: bool = False, secure_cookies: bool = False) -> None:
        self.store = store
        self.demo = demo
        self.secure_cookies = secure_cookies
        self._failures: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()
        routes = [
            ("GET", r"/api/config", self.config, False),
            ("GET", r"/api/me", self.me, True),
            ("POST", r"/api/signup", self.signup, False),
            ("POST", r"/api/login", self.login, False),
            ("POST", r"/api/demo", self.demo_login, False),
            ("POST", r"/api/logout", self.logout, False),
            ("GET", r"/api/dashboard", self.dashboard, True),
            ("GET", r"/api/vaccines", self.vaccines, True),
            ("GET", r"/api/pets", self.pets, True),
            ("POST", r"/api/pets", self.create_pet, True),
            ("GET", r"/api/pets/(\d+)", self.pet, True),
            ("PUT", r"/api/pets/(\d+)", self.update_pet, True),
            ("DELETE", r"/api/pets/(\d+)", self.delete_pet, True),
            ("POST", r"/api/pets/(\d+)/doses", self.add_dose, True),
            ("DELETE", r"/api/doses/(\d+)", self.delete_dose, True),
            ("GET", r"/api/reminders", self.reminders, True),
            ("POST", r"/api/reminders", self.create_reminder, True),
            ("PUT", r"/api/reminders/(\d+)", self.update_reminder, True),
            ("DELETE", r"/api/reminders/(\d+)", self.delete_reminder, True),
            ("POST", r"/api/reminders/(\d+)/complete", self.complete_reminder, True),
            ("GET", r"/api/notifications", self.notifications, True),
            ("POST", r"/api/notifications/read", self.read_notifications, True),
            ("GET", r"/api/calendar", self.calendar_link, True),
        ]
        self.routes = [(m, re.compile(f"^{p}$"), fn, auth) for m, p, fn, auth in routes]

    # session helpers

    def _start_session(self, req: Request, user: dict) -> None:
        token = self.store.create_session(user["id"])
        flags = "; Secure" if self.secure_cookies else ""
        req.set_cookie = f"{COOKIE}={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={30 * 86400}{flags}"

    def _limited(self, email: str) -> bool:
        now = time.monotonic()
        with self._lock:
            q = self._failures[email]
            while q and now - q[0] > LOGIN_WINDOW:
                q.popleft()
            return len(q) >= LOGIN_ATTEMPTS

    def _fail(self, email: str) -> None:
        with self._lock:
            self._failures[email].append(time.monotonic())

    # handlers

    def config(self, req, _):
        return 200, {"demo": self.demo, "species": list(schedule.SPECIES), "repeats": list(schedule.REPEATS)}

    def me(self, req, _):
        return 200, {"user": self._public_user(req.user), "demo": self.demo}

    @staticmethod
    def _public_user(user: dict) -> dict:
        return {"id": user["id"], "name": user["name"], "email": user["email"]}

    def signup(self, req, _):
        data = req.body()
        user = self.store.signup(data.get("name"), data.get("email"), data.get("password"))
        self._start_session(req, user)
        return 201, {"user": self._public_user(user)}

    def login(self, req, _):
        data = req.body()
        email = str(data.get("email") or "").strip().lower()
        if self._limited(email):
            raise ApiError(429, "Too many failed attempts. Wait 15 minutes and try again.")
        try:
            user = self.store.authenticate(email, data.get("password"))
        except ApiError:
            self._fail(email)
            raise
        self._start_session(req, user)
        return 200, {"user": self._public_user(user)}

    def demo_login(self, req, _):
        if not self.demo:
            raise ApiError(404, "Demo mode is not enabled on this server.")
        user = self.store.user_by_email(DEMO_EMAIL)
        if user is None:
            raise ApiError(404, "Demo account is not set up.")
        self._start_session(req, user)
        return 200, {"user": self._public_user(user)}

    def logout(self, req, _):
        self.store.end_session(req.token)
        req.set_cookie = f"{COOKIE}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"
        return 200, {"ok": True}

    def dashboard(self, req, _):
        return 200, self.store.dashboard(req.user["id"])

    def vaccines(self, req, _):
        return 200, {s: [{"code": v.code, "name": v.name, "protects": v.protects, "core": v.core} for v in vs]
                     for s, vs in schedule.VACCINES.items()}

    def pets(self, req, _):
        return 200, {"pets": self.store.list_pets(req.user["id"])}

    def create_pet(self, req, _):
        return 201, self.store.create_pet(req.user["id"], req.body())

    def pet(self, req, m):
        return 200, self.store.get_pet(req.user["id"], int(m[1]))

    def update_pet(self, req, m):
        return 200, self.store.update_pet(req.user["id"], int(m[1]), req.body())

    def delete_pet(self, req, m):
        self.store.delete_pet(req.user["id"], int(m[1]))
        return 200, {"ok": True}

    def add_dose(self, req, m):
        return 201, self.store.add_dose(req.user["id"], int(m[1]), req.body())

    def delete_dose(self, req, m):
        return 200, self.store.delete_dose(req.user["id"], int(m[1]))

    def reminders(self, req, _):
        return 200, self.store.list_reminders(req.user["id"])

    def create_reminder(self, req, _):
        return 201, self.store.create_reminder(req.user["id"], req.body())

    def update_reminder(self, req, m):
        return 200, self.store.update_reminder(req.user["id"], int(m[1]), req.body())

    def delete_reminder(self, req, m):
        self.store.delete_reminder(req.user["id"], int(m[1]))
        return 200, {"ok": True}

    def complete_reminder(self, req, m):
        return 200, self.store.complete_reminder(req.user["id"], int(m[1]))

    def notifications(self, req, _):
        return 200, self.store.notifications(req.user["id"])

    def read_notifications(self, req, _):
        self.store.mark_read(req.user["id"])
        return 200, {"ok": True}

    def calendar_link(self, req, _):
        return 200, {"path": f"/calendar/{req.user['calendar_token']}.ics"}

    # dispatch

    def handle_api(self, req: Request):
        if req.method != "GET" and req.handler.headers.get("X-PetRem") != "1":
            raise ApiError(403, "Missing X-PetRem header.")
        allowed = []
        for method, pattern, fn, auth in self.routes:
            m = pattern.match(req.path)
            if not m:
                continue
            if method != req.method:
                allowed.append(method)
                continue
            if auth and req.user is None:
                raise ApiError(401, "Please log in.")
            return fn(req, m)
        if allowed:
            raise ApiError(405, f"Use {', '.join(allowed)} for this endpoint.")
        raise ApiError(404, "Not found.")


def make_handler(app: App):
    static_root = resources.files("petrem").joinpath("static")

    class Handler(BaseHTTPRequestHandler):
        server_version = "PetRem"
        sys_version = ""

        def log_message(self, fmt, *args) -> None:
            pass

        def _headers(self, status: int, content_type: str, length: int, extra: dict | None = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            self.send_header("X-Frame-Options", "DENY")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()

        def _json(self, status: int, payload, set_cookie: str | None = None) -> None:
            body = json.dumps(payload).encode()
            extra = {"Cache-Control": "no-store"}
            if set_cookie:
                extra["Set-Cookie"] = set_cookie
            self._headers(status, "application/json", len(body), extra)
            if self.command != "HEAD":
                self.wfile.write(body)

        def _dispatch(self) -> None:
            path = urlparse(self.path).path
            if path.startswith("/api/"):
                req = Request(self, app)
                try:
                    status, payload = app.handle_api(req)
                except ApiError as e:
                    status, payload = e.status, {"error": e.message}
                except Exception:
                    status, payload = 500, {"error": "Something went wrong on our side. Please try again."}
                self._json(status, payload, req.set_cookie)
                return
            if self.command not in ("GET", "HEAD"):
                self._json(405, {"error": "Method not allowed."})
                return
            m = re.match(r"^/calendar/([A-Za-z0-9_-]+)\.ics$", path)
            if m:
                found = app.store.calendar_items(m[1])
                if found is None:
                    self._json(404, {"error": "Calendar not found."})
                    return
                body = ics.build(*found).encode()
                self._headers(200, "text/calendar; charset=utf-8", len(body),
                              {"Content-Disposition": 'inline; filename="petrem.ics"', "Cache-Control": "no-store"})
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
            if not path.startswith("/static/") and "." in path.rsplit("/", 1)[-1]:
                self._json(404, {"error": "Not found."})
                return
            name = unquote(path[len("/static/"):]) if path.startswith("/static/") else "index.html"
            if "/" in name or "\\" in name or name.startswith("."):
                self._json(404, {"error": "Not found."})
                return
            target = static_root.joinpath(name)
            suffix = "." + name.rsplit(".", 1)[-1] if "." in name else ""
            if suffix not in STATIC_TYPES or not target.is_file():
                self._json(404, {"error": "Not found."})
                return
            body = target.read_bytes()
            cache = "no-cache" if name == "index.html" else "public, max-age=300"
            self._headers(200, STATIC_TYPES[suffix], len(body),
                          {"Content-Security-Policy": CSP, "Cache-Control": cache})
            if self.command != "HEAD":
                self.wfile.write(body)

        do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = do_PATCH = _dispatch

    return Handler


class Notifier(threading.Thread):
    def __init__(self, store: Store, interval: float = 60.0) -> None:
        super().__init__(daemon=True, name="petrem-notifier")
        self.store = store
        self.interval = interval
        self.stopped = threading.Event()

    def run(self) -> None:
        while not self.stopped.wait(self.interval):
            try:
                self.store.scan()
                self.store.prune_sessions()
            except Exception:
                pass


def make_server(store: Store, host: str = "127.0.0.1", port: int = 8000, demo: bool = False,
                secure_cookies: bool = False) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), make_handler(App(store, demo, secure_cookies)))
    server.daemon_threads = True
    return server
