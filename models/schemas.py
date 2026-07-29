"""Typed data layer for The Rome Lads trip planner.

All persistence rows are converted into these Pydantic models before they reach
the view layer, so views never touch raw sqlite3 tuples.
"""

from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

TRIP_START: date = date(2026, 9, 16)
TRIP_END: date = date(2026, 9, 20)
TRIP_TITLE: str = "The Rome Lads"
TRIP_SUBTITLE: str = "Five days of ruins, ragu and reasonable hydration."


class MediaKind(str, Enum):
    """Type of media stored in the gallery."""

    PHOTO = "photo"
    VIDEO = "video"


class BookingStatus(str, Enum):
    """Lifecycle of an itinerary item."""

    IDEA = "idea"
    PLANNED = "planned"
    BOOKED = "booked"
    DONE = "done"

    @property
    def label(self) -> str:
        """Human-readable label for UI chips."""
        return {"idea": "Idea", "planned": "Planned", "booked": "Booked", "done": "Done"}[self.value]


class Lad(BaseModel):
    """A member of the travelling party."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    name: str
    nickname: str = ""
    home_town: str = ""
    accent: str = "#C7512F"
    notes: str = ""
    avatar_png: bytes | None = None

    @property
    def initials(self) -> str:
        """Two-letter initials used for generated avatars."""
        parts = [p for p in self.name.split() if p]
        return "".join(p[0] for p in parts[:2]).upper() or "?"


class PintEvent(BaseModel):
    """A single pint logged by a lad."""

    id: int
    lad_id: int
    consumed_at: datetime
    venue: str = ""
    beer: str = ""
    note: str = ""


class Badge(BaseModel):
    """An achievement definition, optionally resolved against a lad's total."""

    slug: str
    label: str
    emoji: str
    description: str
    threshold: int
    earned: bool = False


class LeaderboardRow(BaseModel):
    """Aggregated Pint League standing for one lad."""

    lad: Lad
    total: int
    today: int
    rank: int
    badges: list[Badge] = Field(default_factory=list)
    last_pint: datetime | None = None

    @property
    def earned_badges(self) -> list[Badge]:
        """Only the badges this lad has unlocked."""
        return [b for b in self.badges if b.earned]

    @property
    def next_badge(self) -> Badge | None:
        """The cheapest badge still to be unlocked, if any."""
        pending = [b for b in self.badges if not b.earned]
        return min(pending, key=lambda b: b.threshold) if pending else None


class Comment(BaseModel):
    """A comment on a gallery item."""

    id: int
    media_id: int
    author_id: int
    author_name: str = ""
    body: str
    created_at: datetime


class MediaItem(BaseModel):
    """A photo or video in the trip gallery."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    kind: MediaKind
    owner_id: int
    owner_name: str = ""
    caption: str = ""
    day: date
    location: str = ""
    url: str | None = None
    blob: bytes | None = None
    thumb: bytes | None = None
    mime: str = "image/jpeg"
    is_highlight: bool = False
    created_at: datetime
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False


class VoteTally(BaseModel):
    """Vote counts for an activity idea."""

    up: int = 0
    down: int = 0
    my_vote: int = 0

    @property
    def score(self) -> int:
        """Net score used for sorting ideas."""
        return self.up - self.down


class Activity(BaseModel):
    """An itinerary entry for a given trip day."""

    id: int
    day: date
    start_time: time
    end_time: time
    title: str
    category: str = "Sightseeing"
    location: str = ""
    cost_eur: float = 0.0
    status: BookingStatus = BookingStatus.PLANNED
    booking_ref: str = ""
    notes: str = ""
    image_url: str = ""
    sort_order: int = 0
    votes: VoteTally = Field(default_factory=VoteTally)

    @field_validator("cost_eur")
    @classmethod
    def _non_negative(cls, value: float) -> float:
        """Costs may never be negative."""
        return max(0.0, float(value))

    @property
    def duration_hours(self) -> float:
        """Planned duration in fractional hours."""
        start = self.start_time.hour + self.start_time.minute / 60
        end = self.end_time.hour + self.end_time.minute / 60
        return max(0.25, end - start)


def trip_days() -> list[date]:
    """Return every date of the trip, inclusive."""
    span = (TRIP_END - TRIP_START).days
    return [date.fromordinal(TRIP_START.toordinal() + offset) for offset in range(span + 1)]


def day_label(value: date) -> str:
    """Format a trip date as 'Day 3 - Tue 28 Jul'."""
    days = trip_days()
    index = days.index(value) + 1 if value in days else 0
    prefix = f"Day {index} · " if index else ""
    return f"{prefix}{value.strftime('%a %d %b')}"
