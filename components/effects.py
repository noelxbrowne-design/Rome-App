"""Python-generated CSS animations: confetti bursts and progress bars."""

from __future__ import annotations

import random

import streamlit as st

from components.theme import Palette


def confetti(palette: Palette, pieces: int = 90, seed: int | None = None) -> None:
    """Render a one-shot, CSS-only confetti burst.

    No JavaScript is used: every particle's position, delay, colour and spin is
    computed in Python and emitted as inline CSS.

    Args:
        palette: Active palette, used for particle colours.
        pieces: Number of confetti particles.
        seed: Optional RNG seed for reproducible bursts (useful in tests).
    """
    rng = random.Random(seed)
    colours = list(palette.chart_sequence) + ["#F5C542", "#FFFFFF"]
    spans: list[str] = []
    for _ in range(pieces):
        spans.append(
            "<i style='"
            f"left:{rng.uniform(0, 100):.2f}%;"
            f"background:{rng.choice(colours)};"
            f"animation-delay:{rng.uniform(0, 0.9):.2f}s;"
            f"animation-duration:{rng.uniform(2.4, 4.2):.2f}s;"
            f"width:{rng.randint(6, 11)}px;height:{rng.randint(9, 16)}px;"
            f"border-radius:{rng.choice(['2px', '50%'])};"
            f"--rl-spin:{rng.randint(360, 1080)}deg;"
            "'></i>"
        )
    st.markdown(
        f"""
<div class="rl-confetti" aria-hidden="true">{''.join(spans)}</div>
<style>
.rl-confetti {{ position: fixed; inset: 0; pointer-events: none; z-index: 9999; overflow: hidden; }}
.rl-confetti i {{
  position: absolute; top: -8vh; display: block; opacity: 0.95;
  animation-name: rl-confetti-fall; animation-timing-function: cubic-bezier(0.3,0.1,0.4,1);
  animation-fill-mode: forwards;
}}
@keyframes rl-confetti-fall {{
  0%   {{ transform: translateY(0) rotate(0deg); opacity: 1; }}
  85%  {{ opacity: 1; }}
  100% {{ transform: translateY(112vh) rotate(var(--rl-spin)); opacity: 0; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def celebrate(palette: Palette, title: str, subtitle: str) -> None:
    """Show a milestone toast plus a confetti burst."""
    confetti(palette)
    st.markdown(
        f"""
<div class="rl-card rl-animate" role="status" aria-live="polite"
     style="border-color:var(--rl-primary);display:flex;gap:0.9rem;align-items:center;">
  <div style="font-size:2.1rem;animation:rl-pop 0.5s var(--rl-ease) both;">🎉</div>
  <div>
    <div style="font-weight:800;font-size:1.05rem;">{title}</div>
    <div class="rl-muted">{subtitle}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.balloons()


def progress_bar(ratio: float, label: str = "") -> None:
    """Render an animated gradient progress bar with an accessible role."""
    pct = max(0.0, min(1.0, float(ratio))) * 100
    caption = f"<div class='rl-label' style='margin-top:0.5rem'>{label}</div>" if label else ""
    st.markdown(
        f"{caption}<div class='rl-progress' role='progressbar' aria-valuemin='0' aria-valuemax='100' "
        f"aria-valuenow='{pct:.0f}' aria-label='{label or 'Progress'}'>"
        f"<i style='width:{pct:.1f}%'></i></div>",
        unsafe_allow_html=True,
    )
