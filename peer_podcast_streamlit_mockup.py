"""
Streamlit Podcast Note‑Taker – v0.3

Changelog
---------
* **Summary button** moved beside the *Mark this moment* button so all primary controls stay in one row.
* **Editable notes**: every saved key moment now has an inline `st.text_input`; moments are listed **newest‑first**.
* **Transcript toggle bug fixed** – summary/transcript widgets reuse existing session state, preventing rerun wipe‑out.
* **Fallback timer** only appears for local uploads (cannot read `currentTime` from `st.audio`).  Controls are hidden for URL playback.
* Added placeholder comment for live‑podcast / YouTube audio download (e.g. with `yt‑dlp`).
* Minor refactors: global SQLite connection via `st.cache_resource`, smaller helpers.

The code is still an MVP – replace the stubs with real Whisper/LLM calls when ready.
"""

from __future__ import annotations

import hashlib
import io
import os
import sqlite3
import time
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import streamlit as st

# Optional: Whisper, LLM imports
# from whisper import load_model
# import llama_cpp

###############################################################################
# ------------------------- 3rd‑Party Components -----------------------------
###############################################################################
try:
    from streamlit_player import st_player  # type: ignore
    PLAYER_AVAILABLE = True
except ModuleNotFoundError:
    PLAYER_AVAILABLE = False

###############################################################################
# ------------------------- CONFIG & CSS -------------------------------------
###############################################################################
DB_PATH = Path("podcast_cache.db")

st.set_page_config(
    page_title="🎙️ Podcast Note‑Taker",
    layout="centered",
    initial_sidebar_state="collapsed",
)

_MOBILE_CSS = """
<style>
button[kind="primary"]{width:100% !important;}
@media(max-width:600px){.element-container{padding-left:0rem!important;padding-right:0rem!important;}}
</style>
"""
st.markdown(_MOBILE_CSS, unsafe_allow_html=True)

###############################################################################
# ------------------------- HELPERS ------------------------------------------
###############################################################################

@st.cache_resource(show_spinner=False)
def get_db():
    """Reuse a single SQLite connection across reruns."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS cache(
               id TEXT PRIMARY KEY,
               transcript TEXT,
               summary TEXT,
               created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )
    return conn

def hms(sec: float|int) -> str:
    return str(timedelta(seconds=int(sec)))


def file_md5(data: bytes|str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.md5(data).hexdigest()


def cache_get(id_: str) -> Optional[Tuple[str,str]]:
    cur = get_db().execute("SELECT transcript, summary FROM cache WHERE id=?", (id_,))
    row = cur.fetchone()
    return (row[0], row[1]) if row else None


def cache_save(id_: str, transcript: str, summary: str) -> None:
    get_db().execute("REPLACE INTO cache(id,transcript,summary) VALUES (?,?,?)", (id_, transcript, summary))
    get_db().commit()

###############################################################################
# ------------------------- HEAVYWORK (STUBS) --------------------------------
###############################################################################

def transcribe_audio(data: bytes) -> str:
    time.sleep(1)  # simulate latency
    return "[Transcript would go here …]"


def summarize_text(text: str) -> str:
    time.sleep(1)
    return "[Summary generated from transcript …]"

###############################################################################
# ------------------------- APP STATE INIT -----------------------------------
###############################################################################

def init_state():
    st.session_state.setdefault("marks", [])  # List[Dict[str,Any]] – ts, note
    st.session_state.setdefault("summary", None)
    st.session_state.setdefault("transcript", None)
    st.session_state.setdefault("current_time", 0.0)

init_state()

###############################################################################
# ------------------------- UI – SOURCE INPUT --------------------------------
###############################################################################
st.title("🎙️ Podcast Note‑Taker")

audio_bytes: Optional[bytes] = None
file_id: Optional[str] = None
from_url = False

source_tab, upload_tab = st.tabs(["🔗 From URL (best)", "💾 Upload File"])

with source_tab:
    url = st.text_input("Podcast audio URL (MP3/WAV)")
    if url:
        if not PLAYER_AVAILABLE:
            st.error("Install `streamlit-player` for URL playback: `pip install streamlit-player`." )
            st.stop()
        event = st_player(url, controls=True, events=["onProgress"], height=80, key="audio_player")
        if event and getattr(event, "name", "") == "onProgress":
            st.session_state.current_time = event.data.get("playedSeconds", 0)
        # TODO: Download remote audio for transcription → yt‑dlp / requests
        from_url = True
        file_id = file_md5(url)

with upload_tab:
    uploaded = st.file_uploader("Upload audio file", type=["mp3", "wav"])
    if uploaded:
        audio_bytes = uploaded.read()
        st.audio(audio_bytes, format="audio/mp3")
        file_id = file_md5(audio_bytes)
        # Fallback timer (st.audio doesn’t expose currentTime)
        st.markdown("**Playback timer (local uploads)** – optional")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start", key="start_timer"):
                st.session_state.play_start = time.time()
        with col2:
            if st.button("⏸️ Stop", key="stop_timer"):
                st.session_state.pop("play_start", None)
        if "play_start" in st.session_state:
            st.session_state.current_time = time.time() - st.session_state.play_start

# Guard – nothing chosen yet
if file_id is None:
    st.info("Add a podcast first – paste a URL or upload a file.")
    st.stop()

###############################################################################
# ------------------------- UI – CONTROLS ROW --------------------------------
###############################################################################
col_mark, col_summary = st.columns(2)

with col_mark:
    if st.button("🔖 Mark this moment", use_container_width=True):
        st.session_state.marks.append({"ts": st.session_state.current_time, "note": ""})

with col_summary:
    if st.button("✨ Generate summary", type="primary", use_container_width=True):
        cached = cache_get(file_id)
        if cached:
            transcript, summary = cached
        else:
            if from_url:
                st.error("Server‑side download not implemented yet for URL transcription.")
                st.stop()
            with st.spinner("Transcribing …"):
                transcript = transcribe_audio(audio_bytes)  # type: ignore[arg-type]
            with st.spinner("Summarizing …"):
                summary = summarize_text(transcript)
            cache_save(file_id, transcript, summary)
        st.session_state.summary = summary
        st.session_state.transcript = transcript

###############################################################################
# ------------------------- UI – NOW PLAYING ---------------------------------
###############################################################################
st.write(f"**Current position:** {hms(st.session_state.current_time)}")

###############################################################################
# ------------------------- UI – KEY MOMENTS ---------------------------------
###############################################################################
if st.session_state.marks:
    st.subheader("📌 Key moments (newest first)")
    for i, mark in enumerate(sorted(st.session_state.marks, key=lambda m: m["ts"], reverse=True)):
        col1, col2 = st.columns([1,3])
        col1.write(hms(mark["ts"]))
        note_key = f"note_{i}_{int(mark['ts'])}"
        note = col2.text_input("Edit note", value=mark["note"], key=note_key)
        mark["note"] = note  # live update

###############################################################################
# ------------------------- UI – SUMMARY / TRANSCRIPT ------------------------
###############################################################################
if st.session_state.summary:
    st.subheader("📝 Summary")
    st.write(st.session_state.summary)

    if st.checkbox("Show full transcript"):
        st.subheader("📜 Transcript")
        st.write(st.session_state.transcript)

###############################################################################
# ------------------------- DEBUG -------------------------------------------
###############################################################################
with st.expander("⚙️ Debug info"):
    st.json({
        "file_id": file_id,
        "current_time": st.session_state.current_time,
        "marks": st.session_state.marks,
        "summary": bool(st.session_state.summary),
    })
