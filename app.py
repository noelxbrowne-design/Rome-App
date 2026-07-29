"""The Rome Lads - a pure-Python trip planner built with Streamlit.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import sqlite3

import streamlit as st

from components.layout import render_hero, render_nav
from components.theme import current_palette, inject_global_css
from data import repository as repo
from data.database import get_connection, reset_database
from data.seed import seed_if_empty
from models.schemas import TRIP_TITLE
from utils.formatting import euros
from utils.images import avatar_src
from views import photos, pints

PAGE_ICON = "🍺"


def bootstrap() -> sqlite3.Connection:
    """Open the database, apply migrations, seed mock data and restore prefs."""
    connection = get_connection()
    if seed_if_empty(connection):
        st.toast("Seeded the trip with mock data for all six lads.", icon="🇮🇹")
    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = repo.get_setting(connection, "theme_mode", "light")
    if "viewer_id" not in st.session_state:
        lads = repo.list_lads(connection)
        st.session_state["viewer_id"] = lads[0].id if lads else 1
    return connection


def render_sidebar(connection: sqlite3.Connection) -> int:
    """Render the collapsible sidebar (identity, theme toggle, data tools).

    Args:
        connection: Open SQLite connection.

    Returns:
        The id of the lad currently using the app.
    """
    with st.sidebar:
        st.markdown(f"### {PAGE_ICON} {TRIP_TITLE}")
        lads = repo.list_lads(connection)
        names = {lad.id: f"{lad.name} · “{lad.nickname}”" for lad in lads}
        viewer_id = st.selectbox(
            "You are",
            options=list(names),
            format_func=lambda key: names[key],
            index=list(names).index(st.session_state["viewer_id"])
            if st.session_state["viewer_id"] in names else 0,
            help="Likes, comments and votes are recorded against this lad.",
        )
        st.session_state["viewer_id"] = viewer_id

        me = repo.get_lad(connection, viewer_id)
        if me:
            st.markdown(
                f"<div class='rl-card' style='padding:0.7rem 0.8rem;display:flex;gap:0.65rem;align-items:center'>"
                f"<img class='rl-avatar rl-avatar--sm' src='{avatar_src(me.avatar_png, me.name, me.accent)}' "
                f"alt='Profile picture of {me.name}' />"
                f"<div><b>{me.name.split()[0]}</b><div class='rl-muted'>{me.home_town}</div></div></div>",
                unsafe_allow_html=True,
            )

        dark = st.toggle(
            "🌙 Dark mode",
            value=st.session_state["theme_mode"] == "dark",
            help="Switch between the light and dark palettes.",
        )
        mode = "dark" if dark else "light"
        if mode != st.session_state["theme_mode"]:
            st.session_state["theme_mode"] = mode
            repo.set_setting(connection, "theme_mode", mode)
            st.rerun()

        st.divider()
        totals = repo.trip_totals(connection)
        st.metric("Pints logged", int(totals["pints"]))
        st.metric("Gallery items", int(totals["media"]))

        st.divider()
        st.caption("Data is stored locally in SQLite and survives a refresh.")
        if st.button("♻️ Reset trip data", use_container_width=True,
                     help="Wipe everything and re-seed the demo trip"):
            with st.spinner("Resetting the trip..."):
                reset_database(connection)
                seed_if_empty(connection)
            st.session_state.clear()
            st.rerun()

    return int(viewer_id)


def main() -> None:
    """Configure the page, render the shell and route to the active tab."""
    st.set_page_config(
        page_title=f"{TRIP_TITLE} · Rome 2026",
        page_icon=PAGE_ICON,
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={"about": "The Rome Lads - a pure-Python trip planner built with Streamlit."},
    )

    connection = bootstrap()
    palette = current_palette()
    inject_global_css(palette)
    viewer_id = render_sidebar(connection)

    totals = repo.trip_totals(connection)
    standings = repo.leaderboard(connection)
    leader = standings[0].lad.name.split()[0] if standings else "-"
    render_hero(
        (
            (str(int(totals["pints"])), "Pints"),
            (leader, "League leader"),
            (str(int(totals["media"])), "Photos & videos"),
        )
    )

    st.markdown("<div class='rl-sr-only'>Main navigation: Pints, Photos</div>",
                unsafe_allow_html=True)
    active = render_nav()

    if active == "pints":
        pints.render(connection, palette, viewer_id)
    else:
        photos.render(connection, palette, viewer_id)
   

    st.markdown(
        "<div class='rl-muted' style='text-align:center;margin-top:2.5rem'>"
        "Built entirely in Python · Streamlit · Plotly · Pillow · SQLite</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
