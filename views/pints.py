"""Pints tab: the Pint League - leaderboard, stats, timeline, achievements."""

from __future__ import annotations

import sqlite3

import pandas as pd
import streamlit as st

from components import charts, effects
from components.cards import lad_summary_card, pint_timeline
from components.layout import empty_state, section
from components.theme import Palette
from data import repository as repo
from data.seed import trip_day_for_today
from models.schemas import LeaderboardRow, day_label
from utils.badges import BADGE_DEFINITIONS, milestone_reached, progress_to_next
from utils.formatting import escape, relative_time

VENUE_OPTIONS = (
    "Ma Che Siete Venuti a Fa", "Open Baladin", "Scholars Lounge",
    "Bir & Fud, Trastevere", "Terrazza Borromini", "Fiddler's Elbow, Monti", "Elsewhere",
)


def _headline_metrics(standings: list[LeaderboardRow]) -> None:
    """Render the four headline Pint League metrics."""
    total = sum(row.total for row in standings)
    today = sum(row.today for row in standings)
    leader = standings[0] if standings else None
    badges = sum(len(row.earned_badges) for row in standings)
    columns = st.columns(4, gap="medium")
    metrics = (
        ("Pints, all trip", f"{total}", "across six lads"),
        ("Pints today", f"{today}", day_label(trip_day_for_today())),
        ("League leader", leader.lad.name.split()[0] if leader else "-",
         f"{leader.total} pints" if leader else ""),
        ("Badges unlocked", f"{badges}", f"of {len(BADGE_DEFINITIONS) * len(standings)} possible"),
    )
    for column, (label, value, caption) in zip(columns, metrics):
        with column:
            st.markdown(
                f"<div class='rl-card rl-animate'><div class='rl-label'>{label}</div>"
                f"<div class='rl-metric' style='margin-top:0.35rem'>{escape(value)}</div>"
                f"<div class='rl-muted'>{escape(caption)}</div></div>",
                unsafe_allow_html=True,
            )


def _pint_controls(connection: sqlite3.Connection, row: LeaderboardRow) -> None:
    """Render add/remove pint controls and note editing for one lad."""
    add_col, remove_col = st.columns(2, gap="small")
    with add_col:
        if st.button("🍺 Add pint", key=f"add_{row.lad.id}", type="primary",
                     use_container_width=True, help=f"Log a pint for {row.lad.name}"):
            with st.spinner("Pouring..."):
                venue = st.session_state.get(f"venue_{row.lad.id}", "Elsewhere")
                total = repo.add_pint(connection, row.lad.id, venue=venue)
            badge = milestone_reached(total)
            st.session_state["celebration"] = (
                (f"{row.lad.name} unlocked {badge.emoji} {badge.label}!", badge.description)
                if badge
                else None
            )
            st.rerun()
    with remove_col:
        if st.button("↩ Remove pint", key=f"rm_{row.lad.id}", use_container_width=True,
                     help=f"Undo the last pint logged for {row.lad.name}"):
            if repo.remove_last_pint(connection, row.lad.id):
                st.toast(f"Removed a pint from {row.lad.name}.", icon="↩️")
            else:
                st.toast(f"{row.lad.name} has no pints to remove.", icon="🚫")
            st.rerun()

    st.selectbox(
        "Venue for the next round",
        VENUE_OPTIONS,
        key=f"venue_{row.lad.id}",
        help="Attached to the next pint you log for this lad.",
    )

    target, ratio = progress_to_next(row.total)
    next_badge = row.next_badge
    caption = (
        f"{row.total}/{target} towards {next_badge.emoji} {next_badge.label}"
        if next_badge
        else "Every badge unlocked. Legendary."
    )
    effects.progress_bar(ratio, caption)

    with st.expander(f"Personal notes · {row.lad.name}", expanded=False):
        notes = st.text_area(
            "Notes",
            value=row.lad.notes,
            key=f"notes_{row.lad.id}",
            height=110,
            label_visibility="collapsed",
            help="Free-text notes about this lad's trip.",
        )
        if st.button("Save notes", key=f"save_notes_{row.lad.id}", use_container_width=True):
            repo.update_notes(connection, row.lad.id, notes)
            st.toast("Notes saved.", icon="💾")
            st.rerun()


def render(connection: sqlite3.Connection, palette: Palette, viewer_id: int) -> None:
    """Render the complete Pints tab.

    Args:
        connection: Open SQLite connection.
        palette: Active theme palette.
        viewer_id: The lad currently using the app.
    """
    celebration = st.session_state.pop("celebration", None)
    if celebration:
        effects.celebrate(palette, celebration[0], celebration[1])

    with st.spinner("Counting the empties..."):
        standings = repo.leaderboard(connection, today=trip_day_for_today())

    if not standings:
        empty_state("🍺", "No lads yet", "Seed the trip data from the sidebar to get started.")
        return

    _headline_metrics(standings)

    section("Pint League", "Live standings, updated the second a round lands.", "🏆")
    frame = pd.DataFrame(
        [{"name": row.lad.name, "total": row.total, "today": row.today} for row in standings]
    )
    st.plotly_chart(charts.leaderboard_bar(frame, palette), use_container_width=True,
                    config={"displayModeBar": False})

    section("The lads", "Add or remove pints, track badges, keep notes.", "👥")
    for index in range(0, len(standings), 2):
        columns = st.columns(2, gap="medium")
        for column, row in zip(columns, standings[index: index + 2]):
            with column:
                lad_summary_card(row)
                _pint_controls(connection, row)

    section("Daily statistics", "Consumption by day and by lad.", "📊")
    daily = pd.DataFrame(repo.daily_counts(connection))
    daily["day"] = pd.to_datetime(daily["day"])
    left, right = st.columns([3, 2], gap="medium")
    with left:
        st.plotly_chart(charts.daily_area(daily, palette), use_container_width=True,
                        config={"displayModeBar": False})
    with right:
        pivot = (
            daily.pivot_table(index="name", columns=daily["day"].dt.strftime("%a %d"),
                              values="pints", aggfunc="sum", fill_value=0)
            .astype(int)
        )
        pivot["Total"] = pivot.sum(axis=1)
        st.dataframe(pivot.sort_values("Total", ascending=False), use_container_width=True, height=330)

    events = repo.pint_events_frame_rows(connection)
    if events:
        st.plotly_chart(charts.drinks_scatter(pd.DataFrame(events), palette),
                        use_container_width=True, config={"displayModeBar": False})

    section("Timeline of drinks", "The last twenty rounds, newest first.", "🕰️")
    names = repo.lad_names(connection)
    recent = repo.list_pints(connection, limit=20)
    pint_timeline(
        [
            (relative_time(event.consumed_at), names.get(event.lad_id, "Unknown"),
             f"{event.beer or 'Pint'} at {event.venue or 'somewhere in Rome'}")
            for event in recent
        ]
    )

    section("Achievements", "Every badge in the league and who holds it.", "🎖️")
    holders = {
        badge.slug: [row.lad.name.split()[0] for row in standings if row.total >= badge.threshold]
        for badge in BADGE_DEFINITIONS
    }
    columns = st.columns(3, gap="medium")
    for index, badge in enumerate(BADGE_DEFINITIONS):
        who = ", ".join(holders[badge.slug]) or "Nobody yet"
        with columns[index % 3]:
            st.markdown(
                f"<div class='rl-card rl-animate'><div style='font-size:1.7rem'>{badge.emoji}</div>"
                f"<div style='font-weight:750;margin-top:0.3rem'>{escape(badge.label)}</div>"
                f"<div class='rl-muted'>{escape(badge.description)}</div>"
                f"<div class='rl-badges'><span class='rl-chip'>{badge.threshold}+ pints</span>"
                f"<span class='rl-chip rl-chip--muted'>{escape(who)}</span></div></div>",
                unsafe_allow_html=True,
            )
