"""Small presentation helpers shared across views."""

from __future__ import annotations

from datetime import datetime, time


def euros(amount: float) -> str:
    """Format a number as euros with thousands separators."""
    return f"€{amount:,.0f}" if float(amount).is_integer() else f"€{amount:,.2f}"


def time_range(start: time, end: time) -> str:
    """Format a time slot as '09:30 - 12:00'."""
    return f"{start.strftime('%H:%M')} – {end.strftime('%H:%M')}"


def relative_time(moment: datetime, now: datetime | None = None) -> str:
    """Return a compact relative timestamp such as '12m ago' or 'yesterday'."""
    now = now or datetime.now()
    delta = now - moment
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return moment.strftime("%a %d %b, %H:%M")
    if seconds < 60:
        return "just now"
    if seconds < 3_600:
        return f"{seconds // 60}m ago"
    if seconds < 86_400:
        return f"{seconds // 3600}h ago"
    if seconds < 172_800:
        return "yesterday"
    return moment.strftime("%a %d %b, %H:%M")


def truncate(text: str, limit: int = 90) -> str:
    """Truncate text on a word boundary with an ellipsis."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def escape(text: str) -> str:
    """Minimal HTML escaping for user-supplied strings injected into markup."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
