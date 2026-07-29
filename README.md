# The Rome Lads

A premium, mobile-friendly trip companion for six friends in Rome. Three tabs:
**Pints**, **Photos**, **Plans**. Built entirely in Python - no JavaScript,
no React, no Node tooling.

## Stack

| Layer | Choice |
|---|---|
| Web framework | Streamlit (pure Python, native styling APIs) |
| Charts | Plotly Express / Graph Objects, themed from the app palette |
| Images | Pillow (thumbnails, monogram avatars, video posters) |
| Data models | Pydantic v2 |
| Persistence | stdlib sqlite3 (`data/rome_lads.sqlite3`, WAL mode) |

## Quickstart (Python 3.11+)

    python -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    streamlit run app.py

Open http://localhost:8501. The database is created and seeded on first run.

For phone testing on the same network:

    streamlit run app.py --server.address 0.0.0.0

## Using it

- **Sidebar** - pick which lad you are (drives likes, comments and votes),
  toggle dark mode, reset demo data.
- **Pints** - leaderboard, per-lad add/remove pint, animated badge progress,
  daily stats, drinks timeline, achievements. Hitting 1, 3, 10, 15, 20 or 30
  pints fires a CSS confetti celebration.
- **Photos** - upload photos/videos, captions, likes, comments, filter by
  day/person/type, star items into the highlights reel, full-screen viewer.
- **Plans** - day-by-day cards with time slots, cost per person, booking status
  and refs; reorder with arrows; vote up/down; calendar (Gantt) view; cost
  breakdown.

## Notes

- Theme choice and all trip data persist across refreshes.
- Seeded photography loads from Unsplash CDN URLs; uploads are stored as blobs
  with Pillow-generated thumbnails.
- `views/` is used instead of `pages/` on purpose: Streamlit auto-mounts a
  `pages/` folder as extra navigation, which would break the "exactly three
  tabs" requirement.
- Accessibility: semantic section/article/figure markup, alt text on every
  image, aria-labels on ranks and progress bars, visible focus rings,
  `prefers-reduced-motion` support, WCAG AA contrast in both palettes.
- The trip window is hardcoded to 26-30 July 2026 in `models/schemas.py` so
  that "today" lands on day 3 and the daily statistics are populated.
