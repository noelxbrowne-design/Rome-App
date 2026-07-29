"""Page shell: hero, three-tab navigation, section headers, skeleton loaders."""

from __future__ import annotations

from typing import Iterable

import streamlit as st

from models.schemas import TRIP_END, TRIP_START, TRIP_SUBTITLE, TRIP_TITLE

TABS: tuple[tuple[str, str, str], ...] = (
    ("pints", "🍺 Pints", "Pint League standings and stats"),
    ("photos", "📸 Photos", "Photo and video gallery"),
)


def render_hero(stats: Iterable[tuple[str, str]]) -> None:
    """Render the Rome hero banner with headline trip stats.

    Args:
        stats: Pairs of ``(value, label)`` shown as glass stat tiles.
    """
    tiles = "".join(
        f"<div class='rl-hero__stat'><b>{value}</b><span>{label}</span></div>" for value, label in stats
    )
    window = f"{TRIP_START.strftime('%d %b')} – {TRIP_END.strftime('%d %b %Y')}"
    st.markdown(
        f"""
<section class="rl-hero" role="banner"
         aria-label="Rome trip hero image showing the Colosseum at golden hour">
  <div>
    <span class="rl-hero__eyebrow">🇮🇹 Roma · {window}</span>
    <h1 class="rl-hero__title">{TRIP_TITLE}</h1>
    <p class="rl-hero__sub">{TRIP_SUBTITLE}</p>
    <div class="rl-hero__stats">{tiles}</div>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )


def render_nav() -> str:
    """Render the responsive three-tab pill navigation.

    Uses ``st.segmented_control`` when available and falls back to a button row
    that reflows to a single line of thirds on narrow viewports.

    Returns:
        The active tab key: ``"pints"``, ``"photos"`` or ``"plans"``.
    """
    st.session_state.setdefault("active_tab", "pints")
    labels = {key: label for key, label, _ in TABS}
    st.markdown("<div class='rl-nav'>", unsafe_allow_html=True)

    if hasattr(st, "segmented_control"):
        chosen = st.segmented_control(
            "Sections",
            options=[key for key, _, _ in TABS],
            format_func=lambda key: labels[key],
            default=st.session_state["active_tab"],
            key="nav_segments",
            label_visibility="collapsed",
        )
        if chosen:
            st.session_state["active_tab"] = chosen
    else:  # pragma: no cover - older Streamlit runtimes
        columns = st.columns(len(TABS), gap="small")
        for column, (key, label, help_text) in zip(columns, TABS):
            with column:
                active = st.session_state["active_tab"] == key
                if st.button(label, key=f"nav_{key}", help=help_text,
                             type="primary" if active else "secondary", use_container_width=True):
                    st.session_state["active_tab"] = key
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    return str(st.session_state["active_tab"])


def section(title: str, subtitle: str = "", icon: str = "") -> None:
    """Render a consistent section header."""
    prefix = f"{icon} " if icon else ""
    caption = f"<p class='rl-muted' style='margin:0.15rem 0 0'>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"<div style='margin:1.6rem 0 0.85rem'>"
        f"<h2 style='margin:0;font-size:1.35rem'>{prefix}{title}</h2>{caption}</div>",
        unsafe_allow_html=True,
    )


def skeletons(count: int = 3, columns: int = 3) -> None:
    """Render shimmering skeleton placeholders while content loads."""
    cols = st.columns(columns, gap="medium")
    for index in range(count):
        with cols[index % columns]:
            st.markdown("<div class='rl-skeleton'></div>", unsafe_allow_html=True)


def empty_state(icon: str, title: str, body: str) -> None:
    """Render a friendly empty state inside a glass card."""
    st.markdown(
        f"""
<div class="rl-card rl-animate" style="text-align:center;padding:2.2rem 1.2rem;">
  <div style="font-size:2.4rem">{icon}</div>
  <div style="font-weight:750;margin-top:0.45rem">{title}</div>
  <div class="rl-muted" style="margin-top:0.25rem">{body}</div>
</div>
""",
        unsafe_allow_html=True,
    )
