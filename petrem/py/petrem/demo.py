from __future__ import annotations

from datetime import datetime, time, timedelta

from .schedule import add_months
from .store import Store
from .web import DEMO_EMAIL

DEMO_PASSWORD = "petrem-demo"


def seed(store: Store) -> dict:
    """Create (or refresh) a demo account whose data is always relative to today."""
    user = store.user_by_email(DEMO_EMAIL) or store.signup("Alex", DEMO_EMAIL, DEMO_PASSWORD)
    uid = user["id"]
    store.reset_user_data(uid)
    today = store.today()

    def at(days: int, hour: int, minute: int = 0) -> str:
        return datetime.combine(today + timedelta(days=days), time(hour, minute)).isoformat(timespec="minutes")

    puppy_birth = today - timedelta(weeks=14)
    biscuit = store.create_pet(uid, {"name": "Biscuit", "species": "dog", "breed": "Beagle", "sex": "female",
                                     "birth_date": puppy_birth.isoformat(), "weight_kg": 6.2,
                                     "notes": "Loves carrots. Nervous at the vet, bring treats."})
    for weeks in (8, 12):
        store.record_dose_raw(biscuit["id"], "dhpp", puppy_birth + timedelta(weeks=weeks))
    store.record_dose_raw(biscuit["id"], "bordetella", puppy_birth + timedelta(weeks=8))

    cat_birth = add_months(today, -38)
    luna = store.create_pet(uid, {"name": "Luna", "species": "cat", "breed": "Domestic shorthair", "sex": "female",
                                  "birth_date": cat_birth.isoformat(), "weight_kg": 4.1,
                                  "notes": "Indoor cat. Prefers wet food in the evening."})
    for weeks in (8, 12, 16):
        store.record_dose_raw(luna["id"], "fvrcp", cat_birth + timedelta(weeks=weeks))
    store.record_dose_raw(luna["id"], "fvrcp", today - timedelta(days=352))
    store.record_dose_raw(luna["id"], "rabies", today - timedelta(days=400))
    for weeks in (8, 12):
        store.record_dose_raw(luna["id"], "felv", cat_birth + timedelta(weeks=weeks))
    store.record_dose_raw(luna["id"], "felv", today - timedelta(days=150))

    pepper = store.create_pet(uid, {"name": "Pepper", "species": "other", "breed": "Holland Lop rabbit",
                                    "sex": "male", "birth_date": add_months(today, -20).isoformat(), "weight_kg": 1.8})

    reminders = [
        ("Flea & tick treatment", biscuit, at(0, 18), "monthly", "Apply between the shoulder blades."),
        ("Heartworm pill", biscuit, at(5, 8), "monthly", ""),
        ("Annual check-up", luna, at(12, 10, 30), "none", "Ask about dental cleaning."),
        ("Nail trim", pepper, at(3, 17), "monthly", ""),
        ("Buy hay and pellets", pepper, at(1, 12), "none", ""),
        ("Morning walk", biscuit, at(1, 7), "daily", "20 minutes around the park."),
    ]
    for title, pet, due, repeat, notes in reminders:
        store.create_reminder(uid, {"title": title, "pet_id": pet["id"], "due_at": due, "repeat": repeat, "notes": notes})
    done = store.create_reminder(uid, {"title": "Deworming tablet", "pet_id": luna["id"], "due_at": at(-2, 9)})
    store.complete_reminder(uid, done["id"])
    store.scan(uid)
    return user
