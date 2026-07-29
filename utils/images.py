"""Pillow-powered image utilities: thumbnails, avatars, posters, data URIs."""

from __future__ import annotations

import base64
import colorsys
import hashlib
import io

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

THUMB_MAX_SIDE = 900
AVATAR_SIZE = 320


def to_data_uri(payload: bytes, mime: str = "image/jpeg") -> str:
    """Encode raw bytes as a base64 ``data:`` URI for inline HTML rendering."""
    return f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}"


def make_thumbnail(payload: bytes, max_side: int = THUMB_MAX_SIDE) -> bytes:
    """Create a right-side-up, web-sized JPEG thumbnail from uploaded bytes.

    Args:
        payload: Original image bytes (any Pillow-readable format).
        max_side: Longest edge of the produced thumbnail in pixels.

    Returns:
        JPEG-encoded bytes, or the original payload if decoding fails.
    """
    try:
        with Image.open(io.BytesIO(payload)) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((max_side, max_side), Image.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=86, optimize=True, progressive=True)
            return buffer.getvalue()
    except Exception:  # noqa: BLE001 - unreadable upload should not crash the app
        return payload


def _accent_pair(seed: str, accent: str | None = None) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Derive a deterministic two-tone gradient from a seed string."""
    if accent and accent.startswith("#") and len(accent) == 7:
        base = tuple(int(accent[i: i + 2], 16) for i in (1, 3, 5))
    else:
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        hue = digest[0] / 255
        base = tuple(int(c * 255) for c in colorsys.hls_to_rgb(hue, 0.48, 0.62))
    hue, light, sat = colorsys.rgb_to_hls(*[c / 255 for c in base])
    second = tuple(int(c * 255) for c in colorsys.hls_to_rgb((hue + 0.08) % 1.0, min(0.78, light + 0.22), sat))
    return base, second  # type: ignore[return-value]


def _gradient(size: tuple[int, int], start: tuple[int, int, int], end: tuple[int, int, int]) -> Image.Image:
    """Render a smooth diagonal gradient image."""
    width, height = size
    canvas = Image.new("RGB", (width, height), start)
    draw = ImageDraw.Draw(canvas)
    for y in range(height):
        ratio = y / max(1, height - 1)
        colour = tuple(int(start[i] + (end[i] - start[i]) * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=colour)
    return canvas.filter(ImageFilter.GaussianBlur(radius=width / 40))


def _load_font(size: int):
    """Load a bundled TrueType font, falling back to Pillow's default."""
    for candidate in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "Helvetica.ttc", "arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def generate_avatar(name: str, accent: str | None = None, size: int = AVATAR_SIZE) -> bytes:
    """Generate a deterministic gradient monogram avatar as PNG bytes.

    Keeps the app fully self-contained: no bundled photo assets are required
    for the six seeded travellers.
    """
    start, end = _accent_pair(name, accent)
    canvas = _gradient((size, size), start, end)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.ellipse((-size * 0.25, size * 0.55, size * 0.75, size * 1.55), fill=(255, 255, 255, 28))
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "?"
    font = _load_font(int(size * 0.42))
    box = draw.textbbox((0, 0), initials, font=font)
    draw.text(
        ((size - (box[2] - box[0])) / 2 - box[0], (size - (box[3] - box[1])) / 2 - box[1]),
        initials,
        font=font,
        fill=(255, 255, 255, 240),
    )
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def video_poster(label: str, accent: str | None = None, size: tuple[int, int] = (960, 600)) -> bytes:
    """Build a branded poster frame for an uploaded video."""
    start, end = _accent_pair(label, accent)
    canvas = _gradient(size, start, end)
    draw = ImageDraw.Draw(canvas, "RGBA")
    cx, cy = size[0] / 2, size[1] / 2
    draw.ellipse((cx - 62, cy - 62, cx + 62, cy + 62), fill=(255, 255, 255, 58))
    draw.polygon([(cx - 20, cy - 30), (cx - 20, cy + 30), (cx + 30, cy)], fill=(255, 255, 255, 235))
    font = _load_font(30)
    draw.text((36, size[1] - 66), label[:44], font=font, fill=(255, 255, 255, 225))
    buffer = io.BytesIO()
    canvas.save(buffer, format="JPEG", quality=88)
    return buffer.getvalue()


def avatar_src(payload: bytes | None, name: str, accent: str | None = None) -> str:
    """Return a renderable avatar source, generating one on demand if missing."""
    return to_data_uri(payload or generate_avatar(name, accent), "image/png")
