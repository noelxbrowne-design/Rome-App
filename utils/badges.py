"""Achievement engine for the Pint League."""

from __future__ import annotations

from models.schemas import Badge

BADGE_DEFINITIONS: tuple[Badge, ...] = (
    Badge(slug="first_pint", label="First Pint", emoji="🍺",
          description="Broke the seal in Rome.", threshold=1),
    Badge(slug="hat_trick", label="Hat Trick", emoji="🎩",
          description="Three pints in the bag.", threshold=3),
    Badge(slug="double_figures", label="Double Figures", emoji="🔟",
          description="Ten pints across the trip.", threshold=10),
    Badge(slug="rome_veteran", label="Rome Veteran", emoji="🏛️",
          description="Fifteen pints and still walking the Forum.", threshold=15),
    Badge(slug="pub_legend", label="Pub Legend", emoji="👑",
          description="Twenty pints. Songs will be written.", threshold=20),
    Badge(slug="beer_baron", label="Beer Baron", emoji="🦁",
          description="Thirty pints. An empire of foam.", threshold=30),
)

MILESTONES: tuple[int, ...] = tuple(badge.threshold for badge in BADGE_DEFINITIONS)


def badges_for_total(total: int) -> list[Badge]:
    """Return every badge definition, flagged as earned for the given total.

    Args:
        total: Lifetime pint count for a lad.

    Returns:
        A fresh list of :class:`Badge` copies with ``earned`` resolved.
    """
    return [badge.model_copy(update={"earned": total >= badge.threshold}) for badge in BADGE_DEFINITIONS]


def milestone_reached(total: int) -> Badge | None:
    """Return the badge unlocked exactly at ``total``, if any.

    Used to trigger the confetti celebration the moment a pint is logged.
    """
    for badge in BADGE_DEFINITIONS:
        if badge.threshold == total:
            return badge.model_copy(update={"earned": True})
    return None


def progress_to_next(total: int) -> tuple[int, float]:
    """Return the next milestone target and completion ratio in ``[0, 1]``."""
    for threshold in MILESTONES:
        if total < threshold:
            previous = max([m for m in MILESTONES if m <= total], default=0)
            span = max(1, threshold - previous)
            return threshold, min(1.0, (total - previous) / span)
    return MILESTONES[-1], 1.0
