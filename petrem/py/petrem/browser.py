"""Runs the PetRem API inside a browser (Pyodide), so the full app works on static hosting."""
from __future__ import annotations

import io
import json
from datetime import datetime
from urllib.parse import urlparse

from . import ics
from .demo import seed
from .store import ApiError, Store
from .web import App, Request


class _Headers:
    def __init__(self, values: dict) -> None:
        self._values = {k.lower(): str(v) for k, v in values.items()}

    def get(self, key: str, default=None):
        return self._values.get(key.lower(), default)


class _Handler:
    def __init__(self, method: str, path: str, headers: dict, body: bytes) -> None:
        self.command = method
        self.path = path
        self.headers = _Headers({**headers, "Content-Length": len(body)})
        self.rfile = io.BytesIO(body)


class BrowserApp:
    def __init__(self, db_path: str) -> None:
        self._now = datetime.now()
        self.store = Store(db_path, clock=lambda: self._now, hash_iterations=20_000, wal=False)
        seed(self.store)
        self.app = App(self.store, demo=True)

    def handle(self, method: str, url: str, headers_json: str, body: str, now_iso: str) -> str:
        self._now = datetime.fromisoformat(now_iso)
        path = urlparse(url).path
        if path.startswith("/calendar/") and path.endswith(".ics"):
            found = self.store.calendar_items(path[len("/calendar/"):-len(".ics")])
            if found is None:
                return self._out(404, {"error": "Calendar not found."})
            return json.dumps({"status": 200, "type": "text/calendar; charset=utf-8", "body": ics.build(*found), "cookie": None})
        req = Request(_Handler(method, path, json.loads(headers_json), (body or "").encode()), self.app)
        try:
            status, payload = self.app.handle_api(req)
        except ApiError as e:
            status, payload = e.status, {"error": e.message}
        except Exception:
            status, payload = 500, {"error": "Something went wrong. Please reload the page."}
        return self._out(status, payload, req.set_cookie)

    @staticmethod
    def _out(status: int, payload, cookie: str | None = None) -> str:
        return json.dumps({"status": status, "type": "application/json", "body": json.dumps(payload), "cookie": cookie})
