"""All database reads and writes, returning validated Pydantic models."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date, datetime, time

from models.schemas import (
    Activity,
    BookingStatus,
    Comment,
    Lad,
    LeaderboardRow,
    MediaItem,
    MediaKind,
    PintEvent,
    VoteTally,
    trip_days,
)
from utils.badges import badges_for_total

ISO = "%Y-%m-%dT%H:%M:%S"


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
def get_setting(connection: sqlite3.Connection, key: str, default: str = "") -> str:
    """Read a persisted preference (e.g. theme mode)."""
    row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(connection: sqlite3.Connection, key: str, value: str) -> None:
    """Persist a preference so it survives a page refresh."""
    connection.execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


# --------------------------------------------------------------------------- #
# Lads
# --------------------------------------------------------------------------- #
def list_lads(connection: sqlite3.Connection) -> list[Lad]:
    """Return all six travellers ordered by name."""
    rows = connection.execute("SELECT * FROM lads ORDER BY name").fetchall()
    return [Lad(**dict(row)) for row in rows]


def get_lad(connection: sqlite3.Connection, lad_id: int) -> Lad | None:
    """Return a single traveller by id."""
    row = connection.execute("SELECT * FROM lads WHERE id = ?", (lad_id,)).fetchone()
    return Lad(**dict(row)) if row else None


def lad_names(connection: sqlite3.Connection) -> dict[int, str]:
    """Return an ``{id: name}`` lookup for the party."""
    return {lad.id: lad.name for lad in list_lads(connection)}


def update_notes(connection: sqlite3.Connection, lad_id: int, notes: str) -> None:
    """Persist a lad's personal notes."""
    connection.execute("UPDATE lads SET notes = ? WHERE id = ?", (notes.strip(), lad_id))


# --------------------------------------------------------------------------- #
# Pints
# --------------------------------------------------------------------------- #
def add_pint(
    connection: sqlite3.Connection,
    lad_id: int,
    venue: str = "",
    beer: str = "",
    note: str = "",
    consumed_at: datetime | None = None,
) -> int:
    """Log a pint and return the resulting lifetime total for that lad."""
    moment = (consumed_at or datetime.now()).replace(microsecond=0)
    connection.execute(
        "INSERT INTO pints(lad_id, consumed_at, venue, beer, note) VALUES(?,?,?,?,?)",
        (lad_id, moment.strftime(ISO), venue.strip(), beer.strip(), note.strip()),
    )
    return total_pints(connection, lad_id)


def remove_last_pint(connection: sqlite3.Connection, lad_id: int) -> bool:
    """Delete the most recent pint for a lad. Returns ``True`` if one existed."""
    row = connection.execute(
        "SELECT id FROM pints WHERE lad_id = ? ORDER BY consumed_at DESC, id DESC LIMIT 1",
        (lad_id,),
    ).fetchone()
    if not row:
        return False
    connection.execute("DELETE FROM pints WHERE id = ?", (row["id"],))
    return True


def total_pints(connection: sqlite3.Connection, lad_id: int) -> int:
    """Return the lifetime pint count for a lad."""
    row = connection.execute("SELECT COUNT(*) AS n FROM pints WHERE lad_id = ?", (lad_id,)).fetchone()
    return int(row["n"])


def list_pints(connection: sqlite3.Connection, lad_id: int | None = None,
               limit: int | None = None) -> list[PintEvent]:
    """Return pint events, newest first, optionally filtered by lad."""
    sql = "SELECT * FROM pints"
    params: list[object] = []
    if lad_id is not None:
        sql += " WHERE lad_id = ?"
        params.append(lad_id)
    sql += " ORDER BY consumed_at DESC, id DESC"
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    rows = connection.execute(sql, params).fetchall()
    return [
        PintEvent(
            id=row["id"],
            lad_id=row["lad_id"],
            consumed_at=datetime.strptime(row["consumed_at"], ISO),
            venue=row["venue"],
            beer=row["beer"],
            note=row["note"],
        )
        for row in rows
    ]


def leaderboard(connection: sqlite3.Connection, today: date | None = None) -> list[LeaderboardRow]:
    """Compute the full Pint League table with badges and daily counts."""
    today = today or date.today()
    rows = connection.execute(
        """
        SELECT l.id,
               COUNT(p.id) AS total,
               SUM(CASE WHEN substr(p.consumed_at, 1, 10) = ? THEN 1 ELSE 0 END) AS today_count,
               MAX(p.consumed_at) AS last_pint
        FROM lads l
        LEFT JOIN pints p ON p.lad_id = l.id
        GROUP BY l.id
        """,
        (today.isoformat(),),
    ).fetchall()

    lads = {lad.id: lad for lad in list_lads(connection)}
    standings: list[LeaderboardRow] = []
    for row in rows:
        total = int(row["total"] or 0)
        standings.append(
            LeaderboardRow(
                lad=lads[row["id"]],
                total=total,
                today=int(row["today_count"] or 0),
                rank=0,
                badges=badges_for_total(total),
                last_pint=datetime.strptime(row["last_pint"], ISO) if row["last_pint"] else None,
            )
        )

    standings.sort(key=lambda item: (-item.total, item.lad.name))
    for index, entry in enumerate(standings, start=1):
        entry.rank = index
    return standings


def daily_counts(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Return ``{day, name, pints}`` records covering every trip day and lad."""
    rows = connection.execute(
        """
        SELECT substr(p.consumed_at, 1, 10) AS day, l.name AS name, COUNT(*) AS pints
        FROM pints p JOIN lads l ON l.id = p.lad_id
        GROUP BY day, l.name
        """
    ).fetchall()
    tally: dict[tuple[str, str], int] = {(row["day"], row["name"]): int(row["pints"]) for row in rows}
    names = [lad.name for lad in list_lads(connection)]
    return [
        {"day": day.isoformat(), "name": name, "pints": tally.get((day.isoformat(), name), 0)}
        for day in trip_days()
        for name in names
    ]


def pint_events_frame_rows(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Return flattened pint rows for the scatter chart."""
    names = lad_names(connection)
    return [
        {
            "consumed_at": event.consumed_at,
            "name": names.get(event.lad_id, "Unknown"),
            "venue": event.venue or "Somewhere in Rome",
        }
        for event in list_pints(connection)
    ]


# --------------------------------------------------------------------------- #
# Media
# --------------------------------------------------------------------------- #
def _media_from_row(row: sqlite3.Row) -> MediaItem:
    """Convert a joined media row into a :class:`MediaItem`."""
    return MediaItem(
        id=row["id"],
        kind=MediaKind(row["kind"]),
        owner_id=row["owner_id"],
        owner_name=row["owner_name"],
        caption=row["caption"],
        day=date.fromisoformat(row["day"]),
        location=row["location"],
        url=row["url"],
        blob=row["blob"],
        thumb=row["thumb"],
        mime=row["mime"],
        is_highlight=bool(row["is_highlight"]),
        created_at=datetime.strptime(row["created_at"], ISO),
        like_count=int(row["like_count"] or 0),
        comment_count=int(row["comment_count"] or 0),
        liked_by_me=bool(row["liked_by_me"]),
    )


def list_media(
    connection: sqlite3.Connection,
    viewer_id: int,
    day: date | None = None,
    owner_id: int | None = None,
    kind: MediaKind | None = None,
    highlights_only: bool = False,
) -> list[MediaItem]:
    """Return gallery items with like/comment counts, newest first."""
    sql = """
        SELECT m.*, l.name AS owner_name,
               (SELECT COUNT(*) FROM media_likes k WHERE k.media_id = m.id) AS like_count,
               (SELECT COUNT(*) FROM comments c WHERE c.media_id = m.id) AS comment_count,
               EXISTS(SELECT 1 FROM media_likes k2 WHERE k2.media_id = m.id AND k2.lad_id = ?) AS liked_by_me
        FROM media m JOIN lads l ON l.id = m.owner_id
        WHERE 1 = 1
    """
    params: list[object] = [viewer_id]
    if day is not None:
        sql += " AND m.day = ?"
        params.append(day.isoformat())
    if owner_id is not None:
        sql += " AND m.owner_id = ?"
        params.append(owner_id)
    if kind is not None:
        sql += " AND m.kind = ?"
        params.append(kind.value)
    if highlights_only:
        sql += " AND m.is_highlight = 1"
    sql += " ORDER BY m.day DESC, m.created_at DESC, m.id DESC"
    rows = connection.execute(sql, params).fetchall()
    return [_media_from_row(row) for row in rows]


def get_media(connection: sqlite3.Connection, media_id: int, viewer_id: int) -> MediaItem | None:
    """Return a single gallery item for the lightbox."""
    items = [item for item in list_media(connection, viewer_id) if item.id == media_id]
    return items[0] if items else None


def add_media(
    connection: sqlite3.Connection,
    kind: MediaKind,
    owner_id: int,
    day: date,
    caption: str = "",
    location: str = "",
    url: str | None = None,
    blob: bytes | None = None,
    thumb: bytes | None = None,
    mime: str = "image/jpeg",
    is_highlight: bool = False,
) -> int:
    """Insert a photo or video and return its new id."""
    cursor = connection.execute(
        """
        INSERT INTO media(kind, owner_id, caption, day, location, url, blob, thumb, mime, is_highlight, created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            kind.value, owner_id, caption.strip(), day.isoformat(), location.strip(),
            url, blob, thumb, mime, int(is_highlight),
            datetime.now().replace(microsecond=0).strftime(ISO),
        ),
    )
    return int(cursor.lastrowid)


def toggle_like(connection: sqlite3.Connection, media_id: int, lad_id: int) -> bool:
    """Toggle a viewer's like. Returns ``True`` if the item is now liked."""
    existing = connection.execute(
        "SELECT 1 FROM media_likes WHERE media_id = ? AND lad_id = ?", (media_id, lad_id)
    ).fetchone()
    if existing:
        connection.execute("DELETE FROM media_likes WHERE media_id = ? AND lad_id = ?", (media_id, lad_id))
        return False
    connection.execute("INSERT INTO media_likes(media_id, lad_id) VALUES(?, ?)", (media_id, lad_id))
    return True


def set_highlight(connection: sqlite3.Connection, media_id: int, value: bool) -> None:
    """Add or remove an item from the trip highlights reel."""
    connection.execute("UPDATE media SET is_highlight = ? WHERE id = ?", (int(value), media_id))


def update_caption(connection: sqlite3.Connection, media_id: int, caption: str) -> None:
    """Edit a media caption."""
    connection.execute("UPDATE media SET caption = ? WHERE id = ?", (caption.strip(), media_id))


def delete_media(connection: sqlite3.Connection, media_id: int) -> None:
    """Delete a media item and its likes/comments."""
    connection.execute("DELETE FROM media WHERE id = ?", (media_id,))


def add_comment(connection: sqlite3.Connection, media_id: int, author_id: int, body: str) -> None:
    """Attach a comment to a gallery item."""
    connection.execute(
        "INSERT INTO comments(media_id, author_id, body, created_at) VALUES(?,?,?,?)",
        (media_id, author_id, body.strip(), datetime.now().replace(microsecond=0).strftime(ISO)),
    )


def list_comments(connection: sqlite3.Connection, media_id: int) -> list[Comment]:
    """Return comments for an item, oldest first."""
    rows = connection.execute(
        """
        SELECT c.*, l.name AS author_name FROM comments c
        JOIN lads l ON l.id = c.author_id
        WHERE c.media_id = ? ORDER BY c.created_at, c.id
        """,
        (media_id,),
    ).fetchall()
    return [
        Comment(
            id=row["id"],
            media_id=row["media_id"],
            author_id=row["author_id"],
            author_name=row["author_name"],
            body=row["body"],
            created_at=datetime.strptime(row["created_at"], ISO),
        )
        for row in rows
    ]


# --------------------------------------------------------------------------- #
# Activities
# --------------------------------------------------------------------------- #
def _tallies(connection: sqlite3.Connection, viewer_id: int) -> dict[int, VoteTally]:
    """Return vote tallies keyed by activity id."""
    result: dict[int, VoteTally] = defaultdict(VoteTally)
    for row in connection.execute("SELECT activity_id, lad_id, value FROM activity_votes").fetchall():
        tally = result[row["activity_id"]]
        if row["value"] > 0:
            tally.up += 1
        else:
            tally.down += 1
        if row["lad_id"] == viewer_id:
            tally.my_vote = int(row["value"])
    return result


def list_activities(
    connection: sqlite3.Connection,
    viewer_id: int,
    day: date | None = None,
    status: BookingStatus | None = None,
    category: str | None = None,
    max_cost: float | None = None,
) -> list[Activity]:
    """Return itinerary items ordered by day then manual sort order."""
    sql = "SELECT * FROM activities WHERE 1 = 1"
    params: list[object] = []
    if day is not None:
        sql += " AND day = ?"
        params.append(day.isoformat())
    if status is not None:
        sql += " AND status = ?"
        params.append(status.value)
    if category:
        sql += " AND category = ?"
        params.append(category)
    if max_cost is not None:
        sql += " AND cost_eur <= ?"
        params.append(max_cost)
    sql += " ORDER BY day, sort_order, start_time"

    tallies = _tallies(connection, viewer_id)
    activities: list[Activity] = []
    for row in connection.execute(sql, params).fetchall():
        activities.append(
            Activity(
                id=row["id"],
                day=date.fromisoformat(row["day"]),
                start_time=time.fromisoformat(row["start_time"]),
                end_time=time.fromisoformat(row["end_time"]),
                title=row["title"],
                category=row["category"],
                location=row["location"],
                cost_eur=row["cost_eur"],
                status=BookingStatus(row["status"]),
                booking_ref=row["booking_ref"],
                notes=row["notes"],
                image_url=row["image_url"],
                sort_order=row["sort_order"],
                votes=tallies.get(row["id"], VoteTally()),
            )
        )
    return activities


def add_activity(
    connection: sqlite3.Connection,
    day: date,
    start_time: time,
    end_time: time,
    title: str,
    category: str = "Sightseeing",
    location: str = "",
    cost_eur: float = 0.0,
    status: BookingStatus = BookingStatus.IDEA,
    notes: str = "",
    image_url: str = "",
    booking_ref: str = "",
) -> int:
    """Insert an activity at the end of its day and return the new id."""
    row = connection.execute(
        "SELECT COALESCE(MAX(sort_order), 0) + 1 AS next FROM activities WHERE day = ?",
        (day.isoformat(),),
    ).fetchone()
    cursor = connection.execute(
        """
        INSERT INTO activities(day, start_time, end_time, title, category, location,
                               cost_eur, status, booking_ref, notes, image_url, sort_order)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            day.isoformat(), start_time.strftime("%H:%M"), end_time.strftime("%H:%M"), title.strip(),
            category, location.strip(), float(cost_eur), status.value, booking_ref.strip(),
            notes.strip(), image_url.strip(), int(row["next"]),
        ),
    )
    return int(cursor.lastrowid)


def update_activity_field(connection: sqlite3.Connection, activity_id: int, field: str, value: object) -> None:
    """Update one whitelisted activity column."""
    allowed = {"title", "category", "location", "cost_eur", "status", "booking_ref", "notes", "day",
               "start_time", "end_time"}
    if field not in allowed:
        raise ValueError(f"Field {field!r} is not updatable")
    connection.execute(f"UPDATE activities SET {field} = ? WHERE id = ?", (value, activity_id))


def delete_activity(connection: sqlite3.Connection, activity_id: int) -> None:
    """Remove an activity and its votes."""
    connection.execute("DELETE FROM activities WHERE id = ?", (activity_id,))


def move_activity(connection: sqlite3.Connection, activity_id: int, direction: int) -> bool:
    """Swap an activity with its neighbour within the same day.

    Args:
        connection: Open SQLite connection.
        activity_id: Activity to move.
        direction: ``-1`` to move earlier, ``+1`` to move later.

    Returns:
        ``True`` when a swap occurred.
    """
    current = connection.execute(
        "SELECT id, day, sort_order FROM activities WHERE id = ?", (activity_id,)
    ).fetchone()
    if not current:
        return False
    comparator, order = ("<", "DESC") if direction < 0 else (">", "ASC")
    neighbour = connection.execute(
        f"SELECT id, sort_order FROM activities WHERE day = ? AND sort_order {comparator} ? "
        f"ORDER BY sort_order {order} LIMIT 1",
        (current["day"], current["sort_order"]),
    ).fetchone()
    if not neighbour:
        return False
    connection.execute("UPDATE activities SET sort_order = ? WHERE id = ?",
                       (neighbour["sort_order"], current["id"]))
    connection.execute("UPDATE activities SET sort_order = ? WHERE id = ?",
                       (current["sort_order"], neighbour["id"]))
    return True


def cast_vote(connection: sqlite3.Connection, activity_id: int, lad_id: int, value: int) -> None:
    """Cast, change or clear a vote (voting the same way twice clears it)."""
    existing = connection.execute(
        "SELECT value FROM activity_votes WHERE activity_id = ? AND lad_id = ?", (activity_id, lad_id)
    ).fetchone()
    if existing and int(existing["value"]) == value:
        connection.execute("DELETE FROM activity_votes WHERE activity_id = ? AND lad_id = ?",
                           (activity_id, lad_id))
        return
    connection.execute(
        "INSERT INTO activity_votes(activity_id, lad_id, value) VALUES(?,?,?) "
        "ON CONFLICT(activity_id, lad_id) DO UPDATE SET value = excluded.value",
        (activity_id, lad_id, value),
    )


def categories(connection: sqlite3.Connection) -> list[str]:
    """Return the distinct activity categories in use."""
    rows = connection.execute("SELECT DISTINCT category FROM activities ORDER BY category").fetchall()
    return [row["category"] for row in rows]


def trip_totals(connection: sqlite3.Connection) -> dict[str, float]:
    """Return headline counters for the hero section."""
    pints = connection.execute("SELECT COUNT(*) AS n FROM pints").fetchone()["n"]
    media = connection.execute("SELECT COUNT(*) AS n FROM media").fetchone()["n"]
    booked = connection.execute("SELECT COUNT(*) AS n FROM activities WHERE status = 'booked'").fetchone()["n"]
    spend = connection.execute("SELECT COALESCE(SUM(cost_eur), 0) AS s FROM activities").fetchone()["s"]
    return {"pints": float(pints), "media": float(media), "booked": float(booked), "spend": float(spend)}
