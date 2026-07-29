"""Realistic mock data for the six travellers, their pints, media and plans."""

from __future__ import annotations

import random
import sqlite3
from datetime import date, datetime, time

from data import repository as repo
from models.schemas import BookingStatus, MediaKind, trip_days
from utils.images import generate_avatar

LADS: tuple[dict[str, str], ...] = (
    {"name": "Jack Wilde", "nickname": "The Captain", "home_town": "Barntown", "accent": "#C7512F",
     "notes": "Holds the group spreadsheet. Vatican tickets are printed, laminated and in the tote bag."},
    {"name": "Darragh Collins", "nickname": "Ryanair Ronaldo", "home_town": "Murrintown", "accent": "#1F6F63",
     "notes": "Sprinted the terminal in Dublin. Claims the Peroni in Trastevere was purely medicinal."},
    {"name": "Sean Byrne", "nickname": "The Historian", "home_town": "Faythe Harriers", "accent": "#B8791B",
     "notes": "Has three podcasts on the Forum queued. Will explain aqueducts, invited or not."},
    {"name": "Jake Giltrap", "nickname": "Gelato Gains", "home_town": "St. Marys", "accent": "#5B5BD6",
     "notes": "Two gelati a day, minimum. Rating every pistachio in the city out of ten."},
    {"name": "Noel Browne", "nickname": "Sunburn", "home_town": "St Annes", "accent": "#0E7490",
     "notes": "Forgot SPF on day one. Now navigating Rome exclusively via shaded side streets."},
    {"name": "Other", "nickname": "Unknown", "home_town": "Also Unknown", "accent": "#A2456F",
     "notes": "Charmed a free limoncello out of a trattoria in Monti. Will attempt this nightly."},
)

VENUES: tuple[tuple[str, str], ...] = (
    ("Ma Che Siete Venuti a Fa", "Birra del Borgo Re Ale"),
    ("Open Baladin", "Nazionale IPA"),
    ("Scholars Lounge", "Guinness"),
    ("Bir & Fud, Trastevere", "Lupulus Pils"),
    ("Rooftop at Hotel Forum", "Peroni Gran Riserva"),
    ("Abbey Theatre Irish Pub", "Kilkenny"),
    ("Fiddler's Elbow, Monti", "Beamish"),
)


GALLERY: tuple[dict[str, object], ...] = (
    {"offset": 0, "owner": 1, "caption": "Landed. Six lads, one tote bag of laminated tickets.",
     "location": "Roma Termini", "highlight": False,
     "url": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=1100&q=70"},
    {"offset": 0, "owner": 5, "caption": "Trevi at golden hour. Worth the elbows.",
     "location": "Piazza di Trevi", "highlight": True,
     "url": "https://images.unsplash.com/photo-1525874684015-58379d421a52?auto=format&fit=crop&w=1100&q=70"},
    {"offset": 0, "owner": 6, "caption": "Cacio e pepe, night one. Seamus already knows the waiter.",
     "location": "Campo de' Fiori", "highlight": False,
     "url": "https://images.unsplash.com/photo-1533777324565-a040eb52facd?auto=format&fit=crop&w=1100&q=70"},
    {"offset": 1, "owner": 3, "caption": "The Colosseum. Fionn gave a 20-minute unprompted lecture.",
     "location": "Colosseo", "highlight": True,
     "url": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1100&q=70"},
    {"offset": 1, "owner": 2, "caption": "Forum ruins, 34 degrees, zero shade.",
     "location": "Roman Forum", "highlight": False,
     "url": "https://images.unsplash.com/photo-1531572753322-ad063cecc140?auto=format&fit=crop&w=1100&q=70"},
    {"offset": 1, "owner": 4, "caption": "Rooftop pints over the domes. Peak trip so far.",
     "location": "Terrazza Borromini", "highlight": True,
     "url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1100&q=70"},
    {"offset": 2, "owner": 1, "caption": "St Peter's. Ronan took the lift and regrets nothing.",
     "location": "Vatican City", "highlight": False,
     "url": "https://images.unsplash.com/photo-1529260830199-42c24126f198?auto=format&fit=crop&w=1100&q=70"},
    {"offset": 2, "owner": 4, "caption": "Pistachio, 9.4/10. The bar has been raised.",
     "location": "Ponte Sisto", "highlight": False,
     "url": "https://images.unsplash.com/photo-1567206563064-6f60f40a2b57?auto=format&fit=crop&w=1100&q=70"},
    {"offset": 2, "owner": 6, "caption": "Trastevere laneways just before the food tour.",
     "location": "Trastevere", "highlight": True,
     "url": "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=1100&q=70"},
)

COMMENTS: tuple[tuple[int, int, str], ...] = (
    (2, 3, "Historically speaking, that coin toss dates to the 1954 film. You're welcome."),
    (2, 2, "Fionn nobody asked."),
    (4, 5, "I am, factually, the reddest man in Lazio."),
    (6, 1, "Two rounds up here and the budget spreadsheet cried."),
    (6, 4, "Gelato afterwards balanced it out."),
    (9, 6, "The suppli stop alone was worth the flights."),
)


def seed_if_empty(connection: sqlite3.Connection) -> bool:
    """Populate the database with realistic mock data if it is empty.

    Args:
        connection: Open SQLite connection.

    Returns:
        ``True`` if seeding ran, ``False`` if data already existed.
    """
    if connection.execute("SELECT COUNT(*) AS n FROM lads").fetchone()["n"]:
        return False

    rng = random.Random(2026)
    days = trip_days()
    today_index = 2  # trip day 3 is "today" in the seeded narrative

    for lad in LADS:
        connection.execute(
            "INSERT INTO lads(name, nickname, home_town, accent, notes, avatar_png) VALUES(?,?,?,?,?,?)",
            (lad["name"], lad["nickname"], lad["home_town"], lad["accent"], lad["notes"],
             generate_avatar(lad["name"], lad["accent"])),
        )

    per_lad_per_day = {
        1: (4, 5, 2), 2: (6, 7, 3), 3: (3, 4, 1),
        4: (2, 3, 2), 5: (5, 6, 2), 6: (5, 5, 3),
    }
    latest_hour = max(13, datetime.now().hour)
    for lad_id, counts in per_lad_per_day.items():
        for day_index, count in enumerate(counts[: today_index + 1]):
            for _ in range(count):
                venue, beer = rng.choice(VENUES)
                if day_index < today_index:
                    hour = rng.randint(17, 23)
                else:
                    hour = rng.randint(12, min(23, latest_hour))
                moment = datetime.combine(days[day_index], time(hour, rng.choice([5, 17, 28, 41, 52])))
                repo.add_pint(connection, lad_id, venue=venue, beer=beer, consumed_at=moment)


    for item in GALLERY:
        media_id = repo.add_media(
            connection,
            kind=MediaKind.PHOTO,
            owner_id=int(item["owner"]),
            day=days[int(item["offset"])],
            caption=str(item["caption"]),
            location=str(item["location"]),
            url=str(item["url"]),
            is_highlight=bool(item["highlight"]),
        )
        for lad_id in rng.sample(range(1, 7), rng.randint(2, 6)):
            repo.toggle_like(connection, media_id, lad_id)

    for media_id, author_id, body in COMMENTS:
        repo.add_comment(connection, media_id, author_id, body)

    repo.set_setting(connection, "theme_mode", "light")
    return True


def trip_day_for_today() -> date:
    """Return today's date clamped into the trip window for daily stats."""
    today = date.today()
    days = trip_days()
    if today < days[0]:
        return days[0]
    if today > days[-1]:
        return days[-1]
    return today
