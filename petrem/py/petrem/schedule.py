from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class Vaccine:
    code: str
    name: str
    protects: str
    first_weeks: int
    doses: int
    gap_weeks: int
    booster_months: int
    core: bool = True


VACCINES: dict[str, tuple[Vaccine, ...]] = {
    "dog": (
        Vaccine("dhpp", "DHPP", "Distemper, hepatitis, parvovirus and parainfluenza", 8, 3, 4, 12),
        Vaccine("rabies", "Rabies", "Rabies", 16, 1, 0, 12),
        Vaccine("lepto", "Leptospirosis", "Leptospirosis bacteria", 12, 2, 3, 12, core=False),
        Vaccine("bordetella", "Bordetella", "Kennel cough", 8, 1, 0, 12, core=False),
    ),
    "cat": (
        Vaccine("fvrcp", "FVRCP", "Rhinotracheitis, calicivirus and panleukopenia", 8, 3, 4, 12),
        Vaccine("rabies", "Rabies", "Rabies", 16, 1, 0, 12),
        Vaccine("felv", "FeLV", "Feline leukemia virus", 8, 2, 4, 12, core=False),
    ),
    "other": (),
}

SPECIES = tuple(VACCINES)
REPEATS = ("none", "daily", "weekly", "monthly", "yearly")
DUE_SOON_DAYS = 14


def vaccine(species: str, code: str) -> Vaccine | None:
    return next((v for v in VACCINES.get(species, ()) if v.code == code), None)


def add_months(value, months: int):
    index = value.month - 1 + months
    year, month = value.year + index // 12, index % 12 + 1
    return value.replace(year=year, month=month, day=min(value.day, calendar.monthrange(year, month)[1]))


def next_due(v: Vaccine, birth: date, doses: list[date]) -> date:
    if not doses:
        return birth + timedelta(weeks=v.first_weeks)
    last = max(doses)
    if len(doses) < v.doses:
        return last + timedelta(weeks=v.gap_weeks)
    return add_months(last, v.booster_months)


def status(due: date, today: date) -> str:
    days = (due - today).days
    if days < 0:
        return "overdue"
    if days <= DUE_SOON_DAYS:
        return "due_soon"
    return "ok"


def advance(due: datetime, repeat: str) -> datetime | None:
    if repeat == "daily":
        return due + timedelta(days=1)
    if repeat == "weekly":
        return due + timedelta(weeks=1)
    if repeat == "monthly":
        return add_months(due, 1)
    if repeat == "yearly":
        return add_months(due, 12)
    return None


def next_after(due: datetime, repeat: str, now: datetime) -> datetime | None:
    nxt = advance(due, repeat)
    while nxt is not None and nxt <= now:
        nxt = advance(nxt, repeat)
    return nxt


def age_label(birth: date, today: date) -> str:
    months = (today.year - birth.year) * 12 + today.month - birth.month - (today.day < birth.day)
    if months < 1:
        weeks = max(0, (today - birth).days // 7)
        return f"{weeks} week{'s' * (weeks != 1)}"
    if months < 24:
        return f"{months} month{'s' * (months != 1)}"
    return f"{months // 12} years"
