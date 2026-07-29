"""Reusable glass card renderers for lads, media and activities."""

from __future__ import annotations

from typing import Callable

import streamlit as st

from models.schemas import Activity, BookingStatus, LeaderboardRow, MediaItem
from utils.formatting import escape, euros, relative_time, time_range
from utils.images import avatar_src, to_data_uri

RANK_CLASS = {1: "rl-rank--gold", 2: "rl-rank--silver", 3: "rl-rank--bronze"}
STATUS_CLASS = {
    BookingStatus.BOOKED: "rl-chip--success",
    BookingStatus.DONE: "rl-chip--success",
    BookingStatus.PLANNED: "rl-chip--warn",
    BookingStatus.IDEA: "rl-chip--muted",
}


def badge_strip(row: LeaderboardRow) -> str:
    """Return the HTML for a lad's earned achievement chips."""
    if not row.earned_badges:
        return "<div class='rl-muted' style='margin-top:0.5rem'>No badges yet — get a round in.</div>"
    chips = "".join(
        f"<span class='rl-chip rl-badge' title='{escape(badge.description)}'>"
        f"{badge.emoji} {escape(badge.label)}</span>"
        for badge in row.earned_badges
    )
    return f"<div class='rl-badges'>{chips}</div>"


def lad_summary_card(row: LeaderboardRow) -> None:
    """Render the header block of a Pint League card (rank, avatar, totals)."""
    src = avatar_src(row.lad.avatar_png, row.lad.name, row.lad.accent)
    rank_class = RANK_CLASS.get(row.rank, "")
    last = relative_time(row.last_pint) if row.last_pint else "no pints logged"
    st.markdown(
        f"""
<div class="rl-card rl-animate">
  <div class="rl-lad">
    <div class="rl-rank {rank_class}" aria-label="Rank {row.rank}">#{row.rank}</div>
    <img class="rl-avatar" src="{src}"
         alt="Profile picture of {escape(row.lad.name)}" loading="lazy" />
    <div style="flex:1;min-width:0">
      <div style="font-weight:780;font-size:1.05rem">{escape(row.lad.name)}</div>
      <div class="rl-muted">“{escape(row.lad.nickname)}” · last pint {escape(last)}</div>
    </div>
    <div style="text-align:right">
      <div class="rl-metric">{row.total}</div>
      <div class="rl-label">Total · {row.today} today</div>
    </div>
  </div>
  {badge_strip(row)}
</div>
""",
        unsafe_allow_html=True,
    )


def media_tile(item: MediaItem, src: str) -> None:
    """Render a gallery tile with caption overlay and accessible alt text."""
    kind_tag = "▶ VIDEO" if item.kind.value == "video" else "PHOTO"
    star = " ⭐" if item.is_highlight else ""
    alt = escape(item.caption or f"{item.kind.value} from Rome by {item.owner_name}")
    location = (" · " + escape(item.location)) if item.location else ""
    st.markdown(
        f"""
<figure class="rl-media rl-animate" style="margin:0">
  <span class="rl-media__tag">{kind_tag}{star}</span>
  <img src="{src}" alt="{alt}" loading="lazy" />
  <figcaption class="rl-media__overlay">
    <div style="font-weight:700;font-size:0.94rem">{escape(item.caption or 'Untitled')}</div>
    <div style="font-size:0.78rem;opacity:0.9">
      {escape(item.owner_name)} · {item.day.strftime('%a %d %b')}{location}
    </div>
    <div style="font-size:0.78rem;opacity:0.9">
      ❤️ {item.like_count} &nbsp;·&nbsp; 💬 {item.comment_count}
    </div>
  </figcaption>
</figure>
""",
        unsafe_allow_html=True,
    )


def highlight_strip(items: list[MediaItem], resolve_src: Callable[[MediaItem], str]) -> None:
    """Render the horizontally scrollable trip highlights reel."""
    if not items:
        return
    tiles = "".join(
        f"<div><img src='{resolve_src(item)}' alt='Highlight: "
        f"{escape(item.caption or item.location or 'Rome')}' loading='lazy' />"
        f"<div class='rl-muted' style='font-size:0.76rem;margin-top:0.3rem'>"
        f"{escape(item.caption or item.location or 'Rome')}</div></div>"
        for item in items
    )
    st.markdown(
        f"<div class='rl-highlight-strip' role='list' aria-label='Trip highlights'>{tiles}</div>",
        unsafe_allow_html=True,
    )


def activity_card(activity: Activity) -> None:
    """Render an itinerary activity card with time slot, cost and status."""
    status_class = STATUS_CLASS[activity.status]
    cover = (
        f"<img src='{escape(activity.image_url)}' alt='{escape(activity.title)}' loading='lazy' "
        "style='width:100%;height:132px;object-fit:cover;display:block' />"
        if activity.image_url
        else ""
    )
    booking = (
        f"<span class='rl-chip rl-chip--muted'>Ref {escape(activity.booking_ref)}</span>"
        if activity.booking_ref
        else ""
    )
    notes = f"<p class='rl-muted' style='margin:0.55rem 0 0'>{escape(activity.notes)}</p>" if activity.notes else ""
    st.markdown(
        f"""
<article class="rl-card rl-card--flush rl-animate">
  {cover}
  <div class="rl-card__body">
    <div style="display:flex;gap:0.5rem;align-items:baseline;justify-content:space-between">
      <h3 style="margin:0;font-size:1.05rem">{escape(activity.title)}</h3>
      <span class="rl-chip {status_class}">{activity.status.label}</span>
    </div>
    <div class="rl-muted" style="margin-top:0.3rem">
      🕒 {time_range(activity.start_time, activity.end_time)} ·
      📍 {escape(activity.location or 'Rome')} ·
      💶 {euros(activity.cost_eur)} pp
    </div>
    <div class="rl-badges">
      <span class="rl-chip">{escape(activity.category)}</span>
      <span class="rl-chip">👍 {activity.votes.up} · 👎 {activity.votes.down}</span>
      {booking}
    </div>
    {notes}
  </div>
</article>
""",
        unsafe_allow_html=True,
    )


def pint_timeline(events: list[tuple[str, str, str]]) -> None:
    """Render a vertical drinks timeline.

    Args:
        events: Tuples of ``(when, who, what)`` already formatted for display.
    """
    if not events:
        st.markdown("<div class='rl-muted'>No drinks logged yet.</div>", unsafe_allow_html=True)
        return
    rows = "".join(
        f"<li><div style='font-weight:680'>{escape(who)} · {escape(what)}</div>"
        f"<div class='rl-muted'>{escape(when)}</div></li>"
        for when, who, what in events
    )
    st.markdown(
        f"<ul class='rl-timeline' aria-label='Timeline of drinks'>{rows}</ul>",
        unsafe_allow_html=True,
    )


def image_bytes_src(payload: bytes, mime: str = "image/jpeg") -> str:
    """Convenience wrapper turning stored bytes into an inline image source."""
    return to_data_uri(payload, mime)
