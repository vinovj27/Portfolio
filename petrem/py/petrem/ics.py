from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

RRULE = {"daily": "DAILY", "weekly": "WEEKLY", "monthly": "MONTHLY", "yearly": "YEARLY"}


def escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\\n").replace("\n", "\\n"))


def fold(line: str) -> str:
    raw = line.encode()
    if len(raw) <= 75:
        return line
    parts, start = [], 0
    limit = 75
    while start < len(raw):
        end = min(start + limit, len(raw))
        while end < len(raw) and (raw[end] & 0xC0) == 0x80:
            end -= 1
        parts.append(raw[start:end].decode())
        start, limit = end, 74
    return "\r\n ".join(parts)


def build(user: dict, items: list[dict], now: datetime | None = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//PetRem//Pet care reminders//EN", "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH", f"X-WR-CALNAME:{escape('PetRem · ' + user['name'])}", "X-PUBLISHED-TTL:PT1H",
    ]
    for item in items:
        pet = item["pet"]["name"] if item["pet"] else None
        summary = f"{pet}: {item['title']}" if pet else item["title"]
        lines += ["BEGIN:VEVENT", f"UID:petrem-{item['kind']}-{item['id']}@petrem", f"DTSTAMP:{stamp}"]
        if item["kind"] == "vaccine":
            day = date.fromisoformat(item["due"])
            lines += [f"DTSTART;VALUE=DATE:{day:%Y%m%d}", f"DTEND;VALUE=DATE:{day + timedelta(days=1):%Y%m%d}"]
        else:
            start = datetime.fromisoformat(f"{item['due']}T{item['time']}")
            lines += [f"DTSTART:{start:%Y%m%dT%H%M%S}", "DURATION:PT30M"]
            if item["repeat"] in RRULE:
                lines.append(f"RRULE:FREQ={RRULE[item['repeat']]}")
        lines.append(f"SUMMARY:{escape(summary)}")
        if item.get("subtitle"):
            lines.append(f"DESCRIPTION:{escape(item['subtitle'])}")
        trigger = "-P1D" if item["kind"] == "vaccine" else "-PT1H"
        lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{escape(summary)}", f"TRIGGER:{trigger}", "END:VALARM",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in lines) + "\r\n"
