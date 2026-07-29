"""Design system: palettes plus all global CSS, generated from Python."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import streamlit as st

HERO_IMAGE = (
    "https://images.unsplash.com/photo-1552832230-c0197dd311b5"
    "?auto=format&fit=crop&w=2000&q=80"
)


@dataclass(frozen=True, slots=True)
class Palette:
    """A complete colour system for one theme mode."""

    name: str
    bg: str
    bg_alt: str
    surface: str
    surface_strong: str
    border: str
    text: str
    text_muted: str
    primary: str
    primary_soft: str
    accent: str
    success: str
    warning: str
    danger: str
    shadow: str
    grid: str
    chart_sequence: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Expose palette fields for CSS variable generation."""
        return asdict(self)


LIGHT = Palette(
    name="light",
    bg="#FBF8F4",
    bg_alt="#F2ECE4",
    surface="rgba(255, 255, 255, 0.72)",
    surface_strong="rgba(255, 255, 255, 0.94)",
    border="rgba(26, 22, 20, 0.10)",
    text="#1A1614",
    text_muted="#6B625C",
    primary="#C7512F",
    primary_soft="rgba(199, 81, 47, 0.12)",
    accent="#1F6F63",
    success="#1E7A54",
    warning="#B8791B",
    danger="#B3382B",
    shadow="0 18px 48px rgba(38, 27, 20, 0.12)",
    grid="rgba(26, 22, 20, 0.08)",
    chart_sequence=("#C7512F", "#1F6F63", "#B8791B", "#5B5BD6", "#0E7490", "#A2456F"),
)

DARK = Palette(
    name="dark",
    bg="#12100F",
    bg_alt="#1A1716",
    surface="rgba(38, 34, 32, 0.62)",
    surface_strong="rgba(44, 39, 37, 0.92)",
    border="rgba(255, 246, 238, 0.12)",
    text="#F6F1EC",
    text_muted="#B3A79F",
    primary="#F0794F",
    primary_soft="rgba(240, 121, 79, 0.16)",
    accent="#4FD1B8",
    success="#3FBF87",
    warning="#E0A64A",
    danger="#F0765F",
    shadow="0 20px 52px rgba(0, 0, 0, 0.46)",
    grid="rgba(255, 246, 238, 0.10)",
    chart_sequence=("#F0794F", "#4FD1B8", "#E0A64A", "#9A8CFF", "#4FC3E8", "#F58BB4"),
)

PALETTES: dict[str, Palette] = {"light": LIGHT, "dark": DARK}


def current_palette() -> Palette:
    """Return the palette for the active theme mode in session state."""
    return PALETTES[st.session_state.get("theme_mode", "light")]


def _variables(palette: Palette) -> str:
    """Emit the CSS custom properties block for a palette."""
    skip = {"name", "chart_sequence"}
    lines = [
        f"  --rl-{key.replace('_', '-')}: {value};"
        for key, value in palette.as_dict().items()
        if key not in skip
    ]
    return "\n".join(lines)


def inject_global_css(palette: Palette) -> None:
    """Inject the full stylesheet (tokens, glass cards, animations, responsive rules).

    Everything here is produced by Python string composition from the active
    :class:`Palette`, so light/dark mode requires no duplicated hand-written CSS.
    """
    css = f"""
<style>
:root {{
{_variables(palette)}
  --rl-radius: 20px;
  --rl-radius-sm: 12px;
  --rl-gap: 1rem;
  --rl-ease: cubic-bezier(0.22, 0.61, 0.36, 1);
}}

html, body, [data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(1200px 620px at 12% -8%, var(--rl-primary-soft), transparent 60%),
    radial-gradient(900px 500px at 92% 4%, {palette.primary_soft}, transparent 62%),
    linear-gradient(180deg, var(--rl-bg) 0%, var(--rl-bg-alt) 100%);
  color: var(--rl-text);
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stAppViewContainer"] > .main .block-container {{
  padding: 1.1rem 1.4rem 4.5rem;
  max-width: 1240px;
}}
* {{ font-feature-settings: "kern" 1, "liga" 1; }}
h1, h2, h3, h4 {{ letter-spacing: -0.022em; color: var(--rl-text); }}
p, li, label, span {{ color: var(--rl-text); }}

/* ---------- Motion ---------- */
@keyframes rl-rise {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes rl-fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes rl-shimmer {{ 0% {{ background-position: -420px 0; }} 100% {{ background-position: 420px 0; }} }}
@keyframes rl-fill {{ from {{ width: 0%; }} }}
@keyframes rl-float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-6px); }} }}
@keyframes rl-pop {{ 0% {{ transform: scale(0.86); opacity: 0; }} 60% {{ transform: scale(1.06); }} 100% {{ transform: scale(1); opacity: 1; }} }}
.rl-animate {{ animation: rl-rise 0.5s var(--rl-ease) both; }}

/* ---------- Glass surfaces ---------- */
.rl-card {{
  position: relative;
  background: var(--rl-surface);
  border: 1px solid var(--rl-border);
  border-radius: var(--rl-radius);
  box-shadow: var(--rl-shadow);
  backdrop-filter: blur(18px) saturate(140%);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
  padding: 1.15rem 1.25rem;
  transition: transform 0.35s var(--rl-ease), box-shadow 0.35s var(--rl-ease), border-color 0.35s var(--rl-ease);
  animation: rl-rise 0.5s var(--rl-ease) both;
  overflow: hidden;
}}
.rl-card:hover {{ transform: translateY(-3px); border-color: var(--rl-primary); }}
.rl-card--flush {{ padding: 0; }}
.rl-card__body {{ padding: 1rem 1.15rem 1.15rem; }}

/* ---------- Hero ---------- */
.rl-hero {{
  position: relative;
  border-radius: 26px;
  overflow: hidden;
  min-height: 260px;
  display: flex;
  align-items: flex-end;
  padding: clamp(1.2rem, 4vw, 2.4rem);
  color: #fff;
  box-shadow: var(--rl-shadow);
  background-image:
    linear-gradient(190deg, rgba(12,10,9,0.16) 0%, rgba(12,10,9,0.82) 92%),
    url("{HERO_IMAGE}");
  background-size: cover;
  background-position: center 62%;
  animation: rl-fade 0.7s var(--rl-ease) both;
}}
.rl-hero * {{ color: #fff !important; }}
.rl-hero__eyebrow {{
  display: inline-flex; gap: 0.45rem; align-items: center;
  font-size: 0.74rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase;
  background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.28);
  padding: 0.34rem 0.7rem; border-radius: 999px; backdrop-filter: blur(8px);
}}
.rl-hero__title {{ font-size: clamp(2rem, 6.4vw, 3.5rem); font-weight: 800; margin: 0.6rem 0 0.3rem; line-height: 1.02; }}
.rl-hero__sub {{ font-size: clamp(0.95rem, 2.4vw, 1.1rem); max-width: 46ch; opacity: 0.92; margin: 0; }}
.rl-hero__stats {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.1rem; }}
.rl-hero__stat {{
  background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.24);
  border-radius: 14px; padding: 0.5rem 0.8rem; backdrop-filter: blur(10px); min-width: 92px;
}}
.rl-hero__stat b {{ display: block; font-size: 1.22rem; line-height: 1.1; }}
.rl-hero__stat span {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.86; }}

/* ---------- Chips, pills, badges ---------- */
.rl-chip {{
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.24rem 0.62rem; border-radius: 999px; font-size: 0.76rem; font-weight: 600;
  background: var(--rl-primary-soft); color: var(--rl-text);
  border: 1px solid var(--rl-border); white-space: nowrap;
}}
.rl-chip--success {{ background: color-mix(in srgb, var(--rl-success) 16%, transparent); }}
.rl-chip--warn {{ background: color-mix(in srgb, var(--rl-warning) 18%, transparent); }}
.rl-chip--muted {{ background: transparent; color: var(--rl-text-muted); }}
.rl-badges {{ display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.55rem; }}
.rl-badge {{ animation: rl-pop 0.45s var(--rl-ease) both; }}

/* ---------- Lad row ---------- */
.rl-lad {{ display: flex; gap: 0.9rem; align-items: center; }}
.rl-avatar {{
  width: 58px; height: 58px; border-radius: 18px; object-fit: cover;
  border: 2px solid var(--rl-border); box-shadow: 0 8px 20px rgba(0,0,0,0.18);
}}
.rl-avatar--sm {{ width: 34px; height: 34px; border-radius: 11px; }}
.rl-rank {{
  font-variant-numeric: tabular-nums; font-weight: 800; font-size: 1.05rem;
  min-width: 2.4rem; height: 2.4rem; display: grid; place-items: center;
  border-radius: 12px; background: var(--rl-primary-soft); color: var(--rl-primary);
}}
.rl-rank--gold {{ background: linear-gradient(140deg, #F5C542, #E39A16); color: #2A1D05; }}
.rl-rank--silver {{ background: linear-gradient(140deg, #DDE3EA, #A9B4C0); color: #1B2027; }}
.rl-rank--bronze {{ background: linear-gradient(140deg, #E5AE7F, #B9743F); color: #2A1607; }}
.rl-metric {{ font-size: 2rem; font-weight: 800; line-height: 1; font-variant-numeric: tabular-nums; }}
.rl-label {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--rl-text-muted); }}
.rl-muted {{ color: var(--rl-text-muted); font-size: 0.86rem; }}

/* ---------- Progress ---------- */
.rl-progress {{
  height: 10px; border-radius: 999px; background: var(--rl-primary-soft);
  overflow: hidden; margin-top: 0.55rem;
}}
.rl-progress > i {{
  display: block; height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, var(--rl-primary), var(--rl-accent));
  animation: rl-fill 1.05s var(--rl-ease) both;
  box-shadow: 0 0 14px var(--rl-primary-soft);
}}

/* ---------- Timeline ---------- */
.rl-timeline {{ list-style: none; margin: 0; padding: 0 0 0 1.15rem; border-left: 2px dashed var(--rl-border); }}
.rl-timeline li {{ position: relative; padding: 0.5rem 0 0.5rem 0.6rem; animation: rl-rise 0.4s var(--rl-ease) both; }}
.rl-timeline li::before {{
  content: ""; position: absolute; left: -1.52rem; top: 1.05rem;
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--rl-primary); box-shadow: 0 0 0 4px var(--rl-primary-soft);
}}

/* ---------- Media gallery ---------- */
.rl-media {{ position: relative; border-radius: var(--rl-radius); overflow: hidden; border: 1px solid var(--rl-border); }}
.rl-media img {{ width: 100%; display: block; transition: transform 0.6s var(--rl-ease); }}
.rl-media:hover img {{ transform: scale(1.045); }}
.rl-media__overlay {{
  position: absolute; inset: auto 0 0 0; padding: 0.85rem 0.95rem;
  background: linear-gradient(0deg, rgba(8,6,5,0.86), transparent);
  color: #fff; display: flex; flex-direction: column; gap: 0.3rem;
}}
.rl-media__overlay * {{ color: #fff !important; }}
.rl-media__tag {{
  position: absolute; top: 0.7rem; left: 0.7rem; background: rgba(10,8,7,0.6);
  border: 1px solid rgba(255,255,255,0.24); color: #fff !important;
  padding: 0.2rem 0.55rem; border-radius: 999px; font-size: 0.7rem; font-weight: 700;
  backdrop-filter: blur(8px);
}}
.rl-highlight-strip {{ display: flex; gap: 0.7rem; overflow-x: auto; padding: 0.3rem 0.15rem 0.75rem; scroll-snap-type: x mandatory; }}
.rl-highlight-strip > div {{ flex: 0 0 168px; scroll-snap-align: start; animation: rl-float 6s ease-in-out infinite; }}
.rl-highlight-strip img {{ width: 100%; height: 116px; object-fit: cover; border-radius: 16px; border: 1px solid var(--rl-border); }}

/* ---------- Skeletons ---------- */
.rl-skeleton {{
  height: 118px; border-radius: var(--rl-radius);
  background: linear-gradient(90deg, var(--rl-bg-alt) 8%, var(--rl-surface-strong) 24%, var(--rl-bg-alt) 40%);
  background-size: 840px 100%; animation: rl-shimmer 1.25s linear infinite;
}}

/* ---------- Streamlit widget restyling ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  border-radius: 14px; border: 1px solid var(--rl-border);
  background: var(--rl-surface-strong); color: var(--rl-text); font-weight: 650;
  padding: 0.48rem 0.9rem; transition: all 0.24s var(--rl-ease); width: 100%;
}}
.stButton > button:hover, .stFormSubmitButton > button:hover {{
  border-color: var(--rl-primary); color: var(--rl-primary); transform: translateY(-1px);
  box-shadow: 0 10px 22px var(--rl-primary-soft);
}}
.stButton > button:focus-visible, [data-baseweb="tab"]:focus-visible, a:focus-visible, input:focus-visible {{
  outline: 3px solid var(--rl-primary) !important; outline-offset: 2px !important;
}}
button[kind="primary"] {{
  background: linear-gradient(135deg, var(--rl-primary), color-mix(in srgb, var(--rl-primary) 62%, var(--rl-accent))) !important;
  color: #fff !important; border: none !important;
}}
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stForm"] {{
  background: var(--rl-surface); border: 1px solid var(--rl-border);
  border-radius: var(--rl-radius); padding: 0.85rem 1rem;
  backdrop-filter: blur(16px); box-shadow: var(--rl-shadow);
}}
[data-baseweb="tab-list"] {{ gap: 0.4rem; background: transparent; border-bottom: 1px solid var(--rl-border); }}
[data-baseweb="tab"] {{ border-radius: 12px 12px 0 0; font-weight: 650; }}
[data-testid="stFileUploaderDropzone"] {{
  border: 1.5px dashed var(--rl-border); border-radius: var(--rl-radius); background: var(--rl-surface);
}}
div[data-testid="stSpinner"] > div {{ border-top-color: var(--rl-primary) !important; }}
[data-testid="stSidebar"] {{
  background: var(--rl-surface-strong); border-right: 1px solid var(--rl-border);
  backdrop-filter: blur(20px);
}}

/* ---------- Responsive ---------- */
@media (max-width: 1024px) {{
  [data-testid="stAppViewContainer"] > .main .block-container {{ padding: 0.9rem 1rem 4rem; }}
}}
@media (max-width: 640px) {{
  .rl-hero {{ min-height: 218px; border-radius: 20px; }}
  .rl-hero__stats {{ gap: 0.4rem; }}
  .rl-hero__stat {{ flex: 1 1 44%; min-width: 0; }}
  .rl-card {{ padding: 0.95rem 1rem; border-radius: 16px; }}
  .rl-avatar {{ width: 46px; height: 46px; border-radius: 14px; }}
  .rl-metric {{ font-size: 1.6rem; }}
  [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; gap: 0.5rem; }}
  [data-testid="stHorizontalBlock"] > div[data-testid="column"] {{ min-width: 46% !important; flex: 1 1 46% !important; }}
  .rl-nav [data-testid="stHorizontalBlock"] > div[data-testid="column"] {{ min-width: 31% !important; flex: 1 1 31% !important; }}
  [data-baseweb="tab"] {{ font-size: 0.82rem; padding: 0.4rem 0.55rem; }}
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; transition: none !important; }}
}}
.rl-sr-only {{
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0;
}}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


def plotly_layout(palette: Palette) -> dict[str, Any]:
    """Return a Plotly layout dict matching the active palette."""
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": palette.text, "family": "Inter, Segoe UI, system-ui, sans-serif", "size": 13},
        "margin": {"l": 12, "r": 12, "t": 44, "b": 12},
        "hoverlabel": {"bgcolor": palette.bg_alt, "font_color": palette.text, "bordercolor": palette.border},
        "xaxis": {"gridcolor": palette.grid, "zeroline": False, "linecolor": palette.grid},
        "yaxis": {"gridcolor": palette.grid, "zeroline": False, "linecolor": palette.grid},
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0, "title": None},
    }
