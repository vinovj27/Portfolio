from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import date, datetime
from typing import Callable, Iterator

from . import schedule

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash   TEXT NOT NULL,
    calendar_token  TEXT NOT NULL UNIQUE,
    created_at      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash  TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at  REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS pets (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    species     TEXT NOT NULL,
    breed       TEXT NOT NULL DEFAULT '',
    sex         TEXT NOT NULL DEFAULT '',
    birth_date  TEXT NOT NULL,
    weight_kg   REAL,
    color       INTEGER NOT NULL DEFAULT 0,
    notes       TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS doses (
    id        INTEGER PRIMARY KEY,
    pet_id    INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    vaccine   TEXT NOT NULL,
    given_on  TEXT NOT NULL,
    notes     TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS reminders (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pet_id      INTEGER REFERENCES pets(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    notes       TEXT NOT NULL DEFAULT '',
    due_at      TEXT NOT NULL,
    repeat      TEXT NOT NULL DEFAULT 'none',
    done_at     TEXT,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key         TEXT NOT NULL,
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    link        TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    read        INTEGER NOT NULL DEFAULT 0,
    UNIQUE (user_id, key)
);
CREATE INDEX IF NOT EXISTS pets_user ON pets (user_id);
CREATE INDEX IF NOT EXISTS doses_pet ON doses (pet_id);
CREATE INDEX IF NOT EXISTS reminders_user ON reminders (user_id, done_at, due_at);
CREATE INDEX IF NOT EXISTS notifications_user ON notifications (user_id, id);
"""

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_DAYS = 30
PALETTE_SIZE = 8
NOTIFY_VACCINE_DAYS = 7


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _text(data: dict, key: str, limit: int, required: bool = False, label: str | None = None) -> str:
    value = data.get(key, "")
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ApiError(400, f"{label or key.capitalize()} must be text.")
    value = value.strip()
    if required and not value:
        raise ApiError(400, f"{label or key.capitalize()} is required.")
    if len(value) > limit:
        raise ApiError(400, f"{label or key.capitalize()} must be {limit} characters or fewer.")
    return value


def _date(value, label: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ApiError(400, f"{label} must be a valid date (YYYY-MM-DD).") from None


def _datetime(value, label: str) -> datetime:
    try:
        return datetime.fromisoformat(str(value)).replace(second=0, microsecond=0, tzinfo=None)
    except ValueError:
        raise ApiError(400, f"{label} must be a valid date and time.") from None


def _pbkdf2(password: bytes, salt: bytes, iterations: int) -> bytes:
    if hasattr(hashlib, "pbkdf2_hmac"):
        return hashlib.pbkdf2_hmac("sha256", password, salt, iterations)
    inner, outer = hashlib.sha256(), hashlib.sha256()
    key = password if len(password) <= 64 else hashlib.sha256(password).digest()
    key = key.ljust(64, b"\0")
    inner.update(bytes(b ^ 0x36 for b in key))
    outer.update(bytes(b ^ 0x5C for b in key))

    def prf(msg: bytes) -> bytes:
        i, o = inner.copy(), outer.copy()
        i.update(msg)
        o.update(i.digest())
        return o.digest()

    block = u = prf(salt + b"\x00\x00\x00\x01")
    acc = int.from_bytes(block, "big")
    for _ in range(iterations - 1):
        u = prf(u)
        acc ^= int.from_bytes(u, "big")
    return acc.to_bytes(32, "big")


def hash_password(password: str, iterations: int) -> str:
    salt = secrets.token_bytes(16)
    digest = _pbkdf2(password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, digest = stored.split("$")
        check = _pbkdf2(password.encode(), bytes.fromhex(salt), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(check.hex(), digest)


class Store:
    def __init__(self, path: str, clock: Callable[[], datetime] = datetime.now, hash_iterations: int = 240_000,
                 wal: bool = True) -> None:
        self.path = str(path)
        self.clock = clock
        self.iterations = hash_iterations
        self._dummy_hash = hash_password(secrets.token_hex(8), hash_iterations)
        with self.connect() as db:
            if wal:
                db.execute("PRAGMA journal_mode=WAL")
            db.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def now(self) -> datetime:
        return self.clock().replace(second=0, microsecond=0)

    def today(self) -> date:
        return self.clock().date()

    # accounts

    def signup(self, name, email, password) -> dict:
        data = {"name": name, "email": email}
        name = _text(data, "name", 60, required=True)
        email = _text(data, "email", 254, required=True).lower()
        if not EMAIL.match(email):
            raise ApiError(400, "Enter a valid email address.")
        if not isinstance(password, str) or len(password) < 8:
            raise ApiError(400, "Password must be at least 8 characters.")
        if len(password) > 200:
            raise ApiError(400, "Password is too long.")
        with self.connect() as db:
            try:
                cur = db.execute(
                    "INSERT INTO users (name, email, password_hash, calendar_token, created_at) VALUES (?, ?, ?, ?, ?)",
                    (name, email, hash_password(password, self.iterations), secrets.token_urlsafe(24), self.now().isoformat()))
            except sqlite3.IntegrityError:
                raise ApiError(409, "An account with this email already exists. Try logging in.") from None
            return self._user(db, cur.lastrowid)

    def authenticate(self, email, password) -> dict:
        email = (email or "").strip().lower() if isinstance(email, str) else ""
        with self.connect() as db:
            row = db.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,)).fetchone()
            stored = row["password_hash"] if row else self._dummy_hash
            ok = verify_password(password if isinstance(password, str) else "", stored)
            if not row or not ok:
                raise ApiError(401, "Email or password is incorrect.")
            return self._user(db, row["id"])

    def create_session(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                       (hashlib.sha256(token.encode()).hexdigest(), user_id, time.time() + SESSION_DAYS * 86400))
        return token

    def user_for_session(self, token: str | None) -> dict | None:
        if not token:
            return None
        with self.connect() as db:
            row = db.execute("SELECT user_id FROM sessions WHERE token_hash = ? AND expires_at > ?",
                             (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
            return self._user(db, row["user_id"]) if row else None

    def end_session(self, token: str | None) -> None:
        if token:
            with self.connect() as db:
                db.execute("DELETE FROM sessions WHERE token_hash = ?", (hashlib.sha256(token.encode()).hexdigest(),))

    def prune_sessions(self) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM sessions WHERE expires_at <= ?", (time.time(),))

    def user_by_email(self, email: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT id FROM users WHERE email = ?", (email.lower(),)).fetchone()
            return self._user(db, row["id"]) if row else None

    def _user(self, db, user_id: int) -> dict:
        row = db.execute("SELECT id, name, email, calendar_token FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row)

    # pets

    def _clean_pet(self, data: dict) -> dict:
        if not isinstance(data, dict):
            raise ApiError(400, "Expected a JSON object.")
        species = data.get("species")
        if species not in schedule.SPECIES:
            raise ApiError(400, "Species must be dog, cat or other.")
        sex = data.get("sex") or ""
        if sex not in ("", "female", "male"):
            raise ApiError(400, "Sex must be female, male or left blank.")
        birth = _date(data.get("birth_date"), "Birth date")
        if birth > self.today():
            raise ApiError(400, "Birth date can't be in the future.")
        if birth.year < 1980:
            raise ApiError(400, "Birth date looks too far in the past.")
        weight = data.get("weight_kg")
        if weight in ("", None):
            weight = None
        else:
            try:
                weight = round(float(weight), 2)
            except (TypeError, ValueError):
                raise ApiError(400, "Weight must be a number.") from None
            if not 0 < weight <= 200:
                raise ApiError(400, "Weight must be between 0 and 200 kg.")
        return {
            "name": _text(data, "name", 60, required=True),
            "species": species,
            "breed": _text(data, "breed", 60),
            "sex": sex,
            "birth_date": birth.isoformat(),
            "weight_kg": weight,
            "notes": _text(data, "notes", 1000),
        }

    def _pet_row(self, db, user_id: int, pet_id: int) -> sqlite3.Row:
        row = db.execute("SELECT * FROM pets WHERE id = ? AND user_id = ?", (pet_id, user_id)).fetchone()
        if row is None:
            raise ApiError(404, "Pet not found.")
        return row

    def create_pet(self, user_id: int, data: dict) -> dict:
        pet = self._clean_pet(data)
        with self.connect() as db:
            count = db.execute("SELECT COUNT(*) FROM pets WHERE user_id = ?", (user_id,)).fetchone()[0]
            cur = db.execute(
                """INSERT INTO pets (user_id, name, species, breed, sex, birth_date, weight_kg, color, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, pet["name"], pet["species"], pet["breed"], pet["sex"], pet["birth_date"], pet["weight_kg"],
                 count % PALETTE_SIZE, pet["notes"], self.now().isoformat()))
            pet_id = cur.lastrowid
        return self.get_pet(user_id, pet_id)

    def update_pet(self, user_id: int, pet_id: int, data: dict) -> dict:
        pet = self._clean_pet(data)
        with self.connect() as db:
            self._pet_row(db, user_id, pet_id)
            first_dose = db.execute("SELECT MIN(given_on) FROM doses WHERE pet_id = ?", (pet_id,)).fetchone()[0]
            if first_dose and pet["birth_date"] > first_dose:
                raise ApiError(400, "Birth date can't be after a recorded vaccine dose.")
            db.execute(
                "UPDATE pets SET name=?, species=?, breed=?, sex=?, birth_date=?, weight_kg=?, notes=? WHERE id = ?",
                (pet["name"], pet["species"], pet["breed"], pet["sex"], pet["birth_date"], pet["weight_kg"], pet["notes"], pet_id))
            valid = [v.code for v in schedule.VACCINES[pet["species"]]]
            if valid:
                db.execute(f"DELETE FROM doses WHERE pet_id = ? AND vaccine NOT IN ({','.join('?' * len(valid))})",
                           (pet_id, *valid))
            else:
                db.execute("DELETE FROM doses WHERE pet_id = ?", (pet_id,))
        return self.get_pet(user_id, pet_id)

    def delete_pet(self, user_id: int, pet_id: int) -> None:
        with self.connect() as db:
            self._pet_row(db, user_id, pet_id)
            db.execute("DELETE FROM pets WHERE id = ?", (pet_id,))

    def list_pets(self, user_id: int) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM pets WHERE user_id = ? ORDER BY name COLLATE NOCASE", (user_id,)).fetchall()
            return [self._pet_summary(db, row) for row in rows]

    def get_pet(self, user_id: int, pet_id: int) -> dict:
        with self.connect() as db:
            row = self._pet_row(db, user_id, pet_id)
            pet = self._pet_summary(db, row)
            pet["reminders"] = [self._reminder(r, {row["id"]: row}) for r in db.execute(
                "SELECT * FROM reminders WHERE pet_id = ? ORDER BY done_at IS NOT NULL, due_at", (pet_id,))]
            return pet

    def _vaccine_plan(self, db, pet: sqlite3.Row) -> list[dict]:
        today = self.today()
        birth = date.fromisoformat(pet["birth_date"])
        doses: dict[str, list[dict]] = {}
        for d in db.execute("SELECT id, vaccine, given_on, notes FROM doses WHERE pet_id = ? ORDER BY given_on", (pet["id"],)):
            doses.setdefault(d["vaccine"], []).append(dict(d))
        plan = []
        for v in schedule.VACCINES[pet["species"]]:
            given = doses.get(v.code, [])
            due = schedule.next_due(v, birth, [date.fromisoformat(d["given_on"]) for d in given])
            plan.append({
                "code": v.code, "name": v.name, "protects": v.protects, "core": v.core,
                "series": v.doses, "series_done": min(len(given), v.doses), "booster_months": v.booster_months,
                "doses": given, "next_due": due.isoformat(), "days": (due - today).days,
                "status": schedule.status(due, today),
            })
        return plan

    def _pet_summary(self, db, row: sqlite3.Row) -> dict:
        pet = dict(row)
        pet.pop("user_id", None)
        plan = self._vaccine_plan(db, row)
        pet["age"] = schedule.age_label(date.fromisoformat(row["birth_date"]), self.today())
        pet["vaccines"] = plan
        soonest = min(plan, key=lambda v: v["next_due"], default=None)
        pet["next"] = {"name": soonest["name"], "due": soonest["next_due"], "status": soonest["status"],
                       "days": soonest["days"]} if soonest else None
        pet["overdue"] = sum(v["status"] == "overdue" for v in plan)
        return pet

    # doses

    def add_dose(self, user_id: int, pet_id: int, data: dict) -> dict:
        with self.connect() as db:
            pet = self._pet_row(db, user_id, pet_id)
            code = data.get("vaccine")
            v = schedule.vaccine(pet["species"], code)
            if v is None:
                raise ApiError(400, f"Unknown vaccine for a {pet['species']}.")
            given = _date(data.get("given_on"), "Date given")
            if given > self.today():
                raise ApiError(400, "Date given can't be in the future.")
            if given.isoformat() < pet["birth_date"]:
                raise ApiError(400, "Date given can't be before the pet's birth date.")
            dup = db.execute("SELECT 1 FROM doses WHERE pet_id = ? AND vaccine = ? AND given_on = ?",
                             (pet_id, code, given.isoformat())).fetchone()
            if dup:
                raise ApiError(409, f"A {v.name} dose on that date is already recorded.")
            db.execute("INSERT INTO doses (pet_id, vaccine, given_on, notes) VALUES (?, ?, ?, ?)",
                       (pet_id, code, given.isoformat(), _text(data, "notes", 300)))
            db.execute("DELETE FROM notifications WHERE user_id = ? AND key LIKE ?", (user_id, f"v{pet_id}:{code}@%"))
        return self.get_pet(user_id, pet_id)

    def delete_dose(self, user_id: int, dose_id: int) -> dict:
        with self.connect() as db:
            row = db.execute("""SELECT doses.pet_id FROM doses JOIN pets ON pets.id = doses.pet_id
                                WHERE doses.id = ? AND pets.user_id = ?""", (dose_id, user_id)).fetchone()
            if row is None:
                raise ApiError(404, "Dose not found.")
            db.execute("DELETE FROM doses WHERE id = ?", (dose_id,))
        return self.get_pet(user_id, row["pet_id"])

    # reminders

    def _clean_reminder(self, db, user_id: int, data: dict) -> dict:
        if not isinstance(data, dict):
            raise ApiError(400, "Expected a JSON object.")
        repeat = data.get("repeat") or "none"
        if repeat not in schedule.REPEATS:
            raise ApiError(400, "Repeat must be none, daily, weekly, monthly or yearly.")
        pet_id = data.get("pet_id")
        if pet_id in ("", None):
            pet_id = None
        else:
            try:
                pet_id = int(pet_id)
            except (TypeError, ValueError):
                raise ApiError(400, "Pet must be one of your pets.") from None
            self._pet_row(db, user_id, pet_id)
        return {
            "title": _text(data, "title", 100, required=True),
            "notes": _text(data, "notes", 1000),
            "due_at": _datetime(data.get("due_at"), "Due date").isoformat(timespec="minutes"),
            "repeat": repeat,
            "pet_id": pet_id,
        }

    def _reminder_row(self, db, user_id: int, reminder_id: int) -> sqlite3.Row:
        row = db.execute("SELECT * FROM reminders WHERE id = ? AND user_id = ?", (reminder_id, user_id)).fetchone()
        if row is None:
            raise ApiError(404, "Reminder not found.")
        return row

    def _pets_by_id(self, db, user_id: int) -> dict[int, sqlite3.Row]:
        return {r["id"]: r for r in db.execute("SELECT id, name, species, color FROM pets WHERE user_id = ?", (user_id,))}

    @staticmethod
    def _pet_chip(row) -> dict | None:
        return {"id": row["id"], "name": row["name"], "species": row["species"], "color": row["color"]} if row else None

    def _reminder(self, row: sqlite3.Row, pets: dict) -> dict:
        r = dict(row)
        r.pop("user_id", None)
        r["pet"] = self._pet_chip(pets.get(row["pet_id"])) if row["pet_id"] else None
        return r

    def create_reminder(self, user_id: int, data: dict) -> dict:
        with self.connect() as db:
            r = self._clean_reminder(db, user_id, data)
            cur = db.execute(
                "INSERT INTO reminders (user_id, pet_id, title, notes, due_at, repeat, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, r["pet_id"], r["title"], r["notes"], r["due_at"], r["repeat"], self.now().isoformat()))
            return self._reminder(self._reminder_row(db, user_id, cur.lastrowid), self._pets_by_id(db, user_id))

    def update_reminder(self, user_id: int, reminder_id: int, data: dict) -> dict:
        with self.connect() as db:
            self._reminder_row(db, user_id, reminder_id)
            r = self._clean_reminder(db, user_id, data)
            db.execute("UPDATE reminders SET pet_id=?, title=?, notes=?, due_at=?, repeat=?, done_at=NULL WHERE id = ?",
                       (r["pet_id"], r["title"], r["notes"], r["due_at"], r["repeat"], reminder_id))
            return self._reminder(self._reminder_row(db, user_id, reminder_id), self._pets_by_id(db, user_id))

    def delete_reminder(self, user_id: int, reminder_id: int) -> None:
        with self.connect() as db:
            self._reminder_row(db, user_id, reminder_id)
            db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))

    def complete_reminder(self, user_id: int, reminder_id: int) -> dict:
        now = self.now()
        with self.connect() as db:
            row = self._reminder_row(db, user_id, reminder_id)
            if row["done_at"]:
                raise ApiError(409, "This reminder is already done.")
            nxt = schedule.next_after(datetime.fromisoformat(row["due_at"]), row["repeat"], now)
            if nxt is None:
                db.execute("UPDATE reminders SET done_at = ? WHERE id = ?", (now.isoformat(timespec="minutes"), reminder_id))
            else:
                db.execute("UPDATE reminders SET due_at = ? WHERE id = ?", (nxt.isoformat(timespec="minutes"), reminder_id))
            return self._reminder(self._reminder_row(db, user_id, reminder_id), self._pets_by_id(db, user_id))

    def list_reminders(self, user_id: int) -> dict:
        with self.connect() as db:
            pets = self._pets_by_id(db, user_id)
            upcoming = [self._reminder(r, pets) for r in db.execute(
                "SELECT * FROM reminders WHERE user_id = ? AND done_at IS NULL ORDER BY due_at", (user_id,))]
            done = [self._reminder(r, pets) for r in db.execute(
                "SELECT * FROM reminders WHERE user_id = ? AND done_at IS NOT NULL ORDER BY done_at DESC LIMIT 25", (user_id,))]
        return {"upcoming": upcoming, "done": done}

    # dashboard

    def _agenda(self, user_id: int) -> list[dict]:
        items = []
        with self.connect() as db:
            pet_rows = db.execute("SELECT * FROM pets WHERE user_id = ?", (user_id,)).fetchall()
            pets = {p["id"]: p for p in pet_rows}
            for pet in pet_rows:
                for v in self._vaccine_plan(db, pet):
                    items.append({
                        "kind": "vaccine", "id": f"{pet['id']}:{v['code']}", "vaccine": v["code"],
                        "title": f"{v['name']} vaccine", "subtitle": v["protects"],
                        "due": v["next_due"], "time": None, "repeat": "none", "pet": self._pet_chip(pet),
                    })
            for r in db.execute("SELECT * FROM reminders WHERE user_id = ? AND done_at IS NULL", (user_id,)):
                due = datetime.fromisoformat(r["due_at"])
                items.append({
                    "kind": "reminder", "id": r["id"], "title": r["title"], "subtitle": r["notes"],
                    "due": due.date().isoformat(), "time": due.strftime("%H:%M"), "repeat": r["repeat"],
                    "pet": self._pet_chip(pets.get(r["pet_id"])) if r["pet_id"] else None,
                })
        items.sort(key=lambda i: (i["due"], i["time"] or "00:00", i["title"]))
        return items

    def dashboard(self, user_id: int) -> dict:
        today = self.today()
        items = self._agenda(user_id)
        for i in items:
            i["days"] = (date.fromisoformat(i["due"]) - today).days
        overdue = [i for i in items if i["days"] < 0]
        due_today = [i for i in items if i["days"] == 0]
        upcoming = [i for i in items if 0 < i["days"] <= 30][:20]
        with self.connect() as db:
            pet_count = db.execute("SELECT COUNT(*) FROM pets WHERE user_id = ?", (user_id,)).fetchone()[0]
        return {
            "today": today.isoformat(),
            "counts": {"overdue": len(overdue), "today": len(due_today),
                       "week": sum(0 <= i["days"] <= 7 for i in items), "pets": pet_count},
            "overdue": overdue, "due_today": due_today, "upcoming": upcoming,
        }

    # notifications

    def scan(self, user_id: int | None = None) -> int:
        now, today = self.now(), self.today()
        created = 0
        with self.connect() as db:
            users = [user_id] if user_id else [r[0] for r in db.execute("SELECT id FROM users")]
        for uid in users:
            rows = []
            for item in self._agenda(uid):
                due = date.fromisoformat(item["due"])
                pet = item["pet"]["name"] if item["pet"] else None
                if item["kind"] == "reminder":
                    due_at = datetime.fromisoformat(f"{item['due']}T{item['time']}")
                    if due_at <= now:
                        rows.append((f"r{item['id']}@{due_at.isoformat(timespec='minutes')}",
                                     f"Reminder: {item['title']}",
                                     f"{pet + ' · ' if pet else ''}Due {due_at.strftime('%b %d, %H:%M')}",
                                     "#/reminders"))
                elif (due - today).days <= NOTIFY_VACCINE_DAYS:
                    late = (today - due).days
                    when = f"overdue by {late} day{'s' * (late != 1)}" if late > 0 else (
                        "due today" if late == 0 else f"due {due.strftime('%b %d')}")
                    rows.append((f"v{item['id']}@{item['due']}", f"{pet} needs the {item['title']}",
                                 when.capitalize(), f"#/pets/{item['pet']['id']}"))
            with self.connect() as db:
                for key, title, body, link in rows:
                    cur = db.execute(
                        "INSERT OR IGNORE INTO notifications (user_id, key, title, body, link, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (uid, key, title, body, link, now.isoformat(timespec="minutes")))
                    created += cur.rowcount
        return created

    def notifications(self, user_id: int) -> dict:
        self.scan(user_id)
        with self.connect() as db:
            items = [dict(r) for r in db.execute(
                "SELECT id, title, body, link, created_at, read FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT 30",
                (user_id,))]
            unread = db.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = 0", (user_id,)).fetchone()[0]
        return {"items": items, "unread": unread}

    def mark_read(self, user_id: int) -> None:
        with self.connect() as db:
            db.execute("UPDATE notifications SET read = 1 WHERE user_id = ?", (user_id,))

    # calendar feed

    def calendar_items(self, token: str) -> tuple[dict, list[dict]] | None:
        with self.connect() as db:
            row = db.execute("SELECT id FROM users WHERE calendar_token = ?", (token,)).fetchone()
            if row is None:
                return None
            user = self._user(db, row["id"])
        return user, self._agenda(user["id"])

    def reset_user_data(self, user_id: int) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM pets WHERE user_id = ?", (user_id,))
            db.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
            db.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))

    def record_dose_raw(self, pet_id: int, code: str, given_on: date) -> None:
        with self.connect() as db:
            db.execute("INSERT INTO doses (pet_id, vaccine, given_on) VALUES (?, ?, ?)", (pet_id, code, given_on.isoformat()))
