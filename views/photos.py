"""Photos tab: social gallery for photos and videos with a full-screen viewer."""

from __future__ import annotations

import sqlite3

import streamlit as st

from components.cards import highlight_strip, media_tile
from components.layout import empty_state, section
from components.theme import Palette
from data import repository as repo
from models.schemas import MediaItem, MediaKind, day_label, trip_days
from utils.formatting import escape, relative_time
from utils.images import make_thumbnail, to_data_uri, video_poster

IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]
VIDEO_TYPES = ["mp4", "mov", "webm", "m4v"]


def _resolve_src(item: MediaItem) -> str:
    """Return a renderable image source for a gallery item."""
    if item.thumb:
        return to_data_uri(item.thumb, "image/jpeg")
    if item.url:
        return item.url
    if item.blob and item.kind is MediaKind.PHOTO:
        return to_data_uri(item.blob, item.mime)
    return to_data_uri(video_poster(item.caption or "Rome video"), "image/jpeg")


def _open_viewer(media_id: int) -> None:
    """Mark an item to be opened in the full-screen viewer."""
    st.session_state["viewer_media_id"] = media_id


@st.dialog("Media viewer", width="large")
def _viewer(connection: sqlite3.Connection, media_id: int, viewer_id: int) -> None:
    """Full-screen lightbox with likes and comments."""
    item = repo.get_media(connection, media_id, viewer_id)
    if not item:
        st.warning("That item is no longer available.")
        return

    if item.kind is MediaKind.VIDEO and item.blob:
        st.video(item.blob)
    elif item.blob:
        st.image(item.blob, use_container_width=True, caption=item.caption or None)
    elif item.url:
        st.image(item.url, use_container_width=True, caption=item.caption or None)

    location = (" · " + escape(item.location)) if item.location else ""
    st.markdown(
        f"<div class='rl-muted'>{escape(item.owner_name)} · {day_label(item.day)}"
        f"{location} · {relative_time(item.created_at)}</div>",
        unsafe_allow_html=True,
    )

    like_col, star_col, delete_col = st.columns(3, gap="small")
    with like_col:
        label = f"{'❤️' if item.liked_by_me else '🤍'} {item.like_count} likes"
        if st.button(label, key=f"dlg_like_{item.id}", use_container_width=True,
                     help="Like or unlike this item"):
            repo.toggle_like(connection, item.id, viewer_id)
            st.rerun()
    with star_col:
        star_label = "☆ Unhighlight" if item.is_highlight else "⭐ Highlight"
        if st.button(star_label, key=f"dlg_star_{item.id}", use_container_width=True,
                     help="Add or remove this item from the trip highlights reel"):
            repo.set_highlight(connection, item.id, not item.is_highlight)
            st.rerun()
    with delete_col:
        if st.button("🗑 Delete", key=f"dlg_del_{item.id}", use_container_width=True,
                     help="Permanently delete this item"):
            repo.delete_media(connection, item.id)
            st.session_state.pop("viewer_media_id", None)
            st.rerun()

    new_caption = st.text_input("Caption", value=item.caption, key=f"dlg_cap_{item.id}",
                                help="Edit the caption for this item")
    if new_caption != item.caption and st.button("Save caption", key=f"dlg_savecap_{item.id}"):
        repo.update_caption(connection, item.id, new_caption)
        st.rerun()

    st.markdown("#### Comments")
    comments = repo.list_comments(connection, item.id)
    if not comments:
        st.markdown("<div class='rl-muted'>No comments yet. Be the first.</div>", unsafe_allow_html=True)
    for comment in comments:
        st.markdown(
            f"<div class='rl-card' style='padding:0.7rem 0.85rem;margin-bottom:0.45rem'>"
            f"<b>{escape(comment.author_name)}</b> "
            f"<span class='rl-muted'>· {relative_time(comment.created_at)}</span><br/>"
            f"{escape(comment.body)}</div>",
            unsafe_allow_html=True,
        )
    with st.form(f"comment_form_{item.id}", clear_on_submit=True):
        body = st.text_input("Add a comment", key=f"dlg_new_comment_{item.id}",
                             placeholder="Say something...")
        if st.form_submit_button("Post comment", type="primary") and body.strip():
            repo.add_comment(connection, item.id, viewer_id, body)
            st.rerun()


def _upload_panel(connection: sqlite3.Connection, viewer_id: int) -> None:
    """Render the upload form for photos and videos."""
    with st.expander("⬆️ Upload photos or videos", expanded=False):
        with st.form("upload_form", clear_on_submit=True):
            files = st.file_uploader(
                "Choose files",
                type=IMAGE_TYPES + VIDEO_TYPES,
                accept_multiple_files=True,
                help="Photos are thumbnailed automatically; videos are stored as uploaded.",
            )
            left, right = st.columns(2, gap="medium")
            with left:
                caption = st.text_input("Caption", placeholder="Rooftop pints over the domes")
                chosen_day = st.selectbox("Trip day", trip_days(), format_func=day_label,
                                          index=min(2, len(trip_days()) - 1))
            with right:
                location = st.text_input("Location", placeholder="Terrazza Borromini")
                highlight = st.checkbox("Add to trip highlights", value=False)
            submitted = st.form_submit_button("Upload", type="primary", use_container_width=True)

        if submitted and files:
            progress = st.progress(0.0, text="Processing uploads...")
            for index, upload in enumerate(files, start=1):
                payload = upload.getvalue()
                extension = upload.name.rsplit(".", 1)[-1].lower()
                is_video = extension in VIDEO_TYPES
                with st.spinner(f"Optimising {upload.name}..."):
                    thumb = video_poster(caption or upload.name) if is_video else make_thumbnail(payload)
                    repo.add_media(
                        connection,
                        kind=MediaKind.VIDEO if is_video else MediaKind.PHOTO,
                        owner_id=viewer_id,
                        day=chosen_day,
                        caption=caption,
                        location=location,
                        blob=payload,
                        thumb=thumb,
                        mime=upload.type or ("video/mp4" if is_video else "image/jpeg"),
                        is_highlight=highlight,
                    )
                progress.progress(index / len(files), text=f"Uploaded {index} of {len(files)}")
            progress.empty()
            st.toast(f"Added {len(files)} item(s) to the gallery.", icon="📸")
            st.rerun()
        elif submitted:
            st.warning("Pick at least one file to upload.")


def render(connection: sqlite3.Connection, palette: Palette, viewer_id: int) -> None:
    """Render the complete Photos tab.

    Args:
        connection: Open SQLite connection.
        palette: Active theme palette.
        viewer_id: The lad currently using the app.
    """
    if st.session_state.get("viewer_media_id"):
        _viewer(connection, int(st.session_state.pop("viewer_media_id")), viewer_id)

    lads = repo.list_lads(connection)
    name_by_id = {lad.id: lad.name for lad in lads}

    section("Trip highlights", "The shots that will end up framed.", "⭐")
    highlights = repo.list_media(connection, viewer_id, highlights_only=True)
    if highlights:
        highlight_strip(highlights, _resolve_src)
    else:
        st.markdown("<div class='rl-muted'>No highlights picked yet - star a photo to add it.</div>",
                    unsafe_allow_html=True)

    _upload_panel(connection, viewer_id)

    section("Gallery", "Filter by day, person or media type.", "📸")
    filter_cols = st.columns([2, 2, 2, 2], gap="medium")
    with filter_cols[0]:
        day_choice = st.selectbox("Day", ["All days"] + trip_days(),
                                  format_func=lambda v: v if isinstance(v, str) else day_label(v))
    with filter_cols[1]:
        person_choice = st.selectbox("Person", ["Everyone"] + [lad.id for lad in lads],
                                     format_func=lambda v: v if isinstance(v, str) else name_by_id[v])
    with filter_cols[2]:
        kind_choice = st.selectbox("Media type", ["All", "Photos", "Videos"])
    with filter_cols[3]:
        density = st.select_slider("Columns", options=[1, 2, 3, 4], value=3,
                                   help="Gallery density - 1 is best on a phone.")

    kind = {"Photos": MediaKind.PHOTO, "Videos": MediaKind.VIDEO}.get(str(kind_choice))
    with st.spinner("Loading the gallery..."):
        items = repo.list_media(
            connection,
            viewer_id,
            day=None if isinstance(day_choice, str) else day_choice,
            owner_id=None if isinstance(person_choice, str) else int(person_choice),
            kind=kind,
        )

    if not items:
        empty_state("🖼️", "Nothing matches those filters",
                    "Try widening the day or person filter.")
        return

    st.markdown(f"<div class='rl-muted'>{len(items)} item(s)</div>", unsafe_allow_html=True)

    columns = st.columns(int(density), gap="medium")
    for index, item in enumerate(items):
        with columns[index % int(density)]:
            media_tile(item, _resolve_src(item))
            action_cols = st.columns(3, gap="small")
            with action_cols[0]:
                heart = "❤️" if item.liked_by_me else "🤍"
                if st.button(f"{heart} {item.like_count}", key=f"like_{item.id}",
                             use_container_width=True, help=f"Like this {item.kind.value}"):
                    repo.toggle_like(connection, item.id, viewer_id)
                    st.rerun()
            with action_cols[1]:
                if st.button(f"💬 {item.comment_count}", key=f"cmt_{item.id}",
                             use_container_width=True, help="Open comments"):
                    _open_viewer(item.id)
                    st.rerun()
            with action_cols[2]:
                if st.button("⛶ Open", key=f"open_{item.id}", use_container_width=True,
                             help="View full screen"):
                    _open_viewer(item.id)
                    st.rerun()
