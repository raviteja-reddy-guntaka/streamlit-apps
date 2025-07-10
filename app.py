# import streamlit as st

# st.title("Basic Housing Price Prediction Model with analysis")

# st.markdown(":blue-badge[Home]")

# st.badge("Home", color="blue")

# st.audio_input("Start recording your voice here:")

# st.slider("Use this slider to  set the variation in voice.")

# st.text_area("Enter your input here")

# file: app.py
import streamlit as st
import time
from datetime import timedelta

st.set_page_config(page_title="🎙️ Podcast Note-Taker", layout="wide")

# ---------- Helpers ----------
def init_state():
    if "marks" not in st.session_state:
        st.session_state.marks = []          # list of (timestamp, label)
    if "play_start" not in st.session_state:
        st.session_state.play_start = None   # wall-clock when user hit Play

def fake_current_time():
    """Mock the 'current playback position'."""
    if st.session_state.play_start is None:
        return 0
    return int(time.time() - st.session_state.play_start)

def hms(sec: int) -> str:
    return str(timedelta(seconds=sec))

# ---------- UI ----------
init_state()
st.title("🎙️ Podcast Note-Taker (MVP)")

# 1. Load audio -------------------------------------------------------------
with st.sidebar:
    st.header("Load podcast")
    audio_file = st.file_uploader("Upload MP3 / WAV", type=["mp3", "wav"])
    demo_clip = st.checkbox("Use built-in demo clip")

if demo_clip:
    import base64, pathlib
    demo_path = pathlib.Path(__file__).parent / "demo.mp3"
    audio_file = demo_path.open("rb")

# 2. Audio player + mock play/stop -----------------------------------------
if audio_file:
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format="audio/mp3")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Play (mock)"):
            st.session_state.play_start = time.time()      # store wall clock
    with col2:
        if st.button("⏸️ Stop"):
            st.session_state.play_start = None
    with col3:
        if st.button("🔖 Mark this moment"):
            ts = fake_current_time()
            st.session_state.marks.append((ts, f"Moment {len(st.session_state.marks)+1}"))

    # Display running clock (mock)
    st.write(f"Current position: **{hms(fake_current_time())}**")

# 3. Show saved key moments -------------------------------------------------
if st.session_state.marks:
    st.subheader("📌 Your key moments")
    for t, label in st.session_state.marks:
        st.write(f"• {label} — {hms(t)}")

# 4. Summary button ---------------------------------------------------------
if st.button("✨ Generate summary (placeholder)"):
    # ——— Placeholder for: Whisper → transcript → LLM summarization ———
    st.spinner("Transcribing & summarizing …")
    st.success("Done!")
    st.subheader("📝 Auto-generated summary")
    st.write("_This is where the LLM output will appear._")

st.caption("⏳ Timestamp accuracy will improve once the real audio-time hook is wired in.")
