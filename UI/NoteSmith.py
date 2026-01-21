from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------
# Ensure project root is in PYTHONPATH (for `agent`, `tools`, `shared`)
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.agent import summarize_file_for_exam  # noqa: E402
from shared.length_utils import target_words_from_length  # noqa: E402


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def detect_direction(text: str) -> str:
    """Detect RTL if Hebrew characters exist."""
    return "rtl" if re.search(r"[\u0590-\u05FF]", text) else "ltr"


# ---------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="NoteSmith – AI Exam Summarizer",
    page_icon="📘",
    layout="wide",
)

# ---------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;700&display=swap');

html, body, [class*="css"]  {
  font-family: 'Assistant', system-ui, -apple-system, Segoe UI, Roboto, Arial !important;
}

.card {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  border: 1px solid rgba(49, 51, 63, 0.18);
  border-radius: 16px;
  padding: 18px 22px;
  background: rgba(255,255,255,0.04);
  box-shadow: 0 8px 22px rgba(0,0,0,0.07);
}

.meta {
  font-size: 0.95rem;
  opacity: 0.86;
  margin-bottom: 10px;
}

.rtl { direction: rtl; text-align: right; }
.ltr { direction: ltr; text-align: left; }

.rtl h1, .rtl h2, .rtl h3, .rtl h4 {
  text-align: right;
}

.small-note {
  font-size: 0.85rem;
  opacity: 0.75;
  margin-top: 6px;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
}
.stTabs [data-baseweb="tab"] {
  height: 40px;
  border-radius: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.title("📘 NoteSmith")
st.caption("Upload a document and get an exam-focused summary in Hebrew.")
st.divider()

# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Settings")

    uploaded_file = st.file_uploader(
        "Upload (PDF / TXT / DOCX)",
        type=["pdf", "txt", "docx"],
    )

    length_ui = st.radio(
        "Summary length",
        options=["Half page", "One page", "2–3 pages"],
        index=1,
    )

    length_map = {
        "Half page": "half_page",
        "One page": "one_page",
        "2–3 pages": "two_three_pages",
    }

    base_words = target_words_from_length(length_map[length_ui])

    custom_words = st.number_input(
        "Custom word target (optional)",
        min_value=100,
        max_value=4000,
        value=int(base_words),
        step=50,
        help="Overrides the preset length when changed.",
    )

    st.caption("The app targets a word count range and auto-adjusts length for accuracy.")

    summarize_clicked = st.button("✨ Summarize", use_container_width=True)

# ---------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------
left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("How it works")
    st.write(
        "- Extracts text from the uploaded file\n"
        "- Counts tokens to decide chunking\n"
        "- Summarizes using a numeric word target\n"
        "- Adjusts length for exam accuracy\n"
        "- Allows preview and export"
    )
    st.info("Tip: Scanned PDFs may require OCR (planned feature).")

with right:
    st.subheader("Output")

    if summarize_clicked:
        if uploaded_file is None:
            st.error("Please upload a file first.")
        else:
            suffix = Path(uploaded_file.name).suffix.lower()

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            try:
                override = (
                    int(custom_words)
                    if int(custom_words) != int(base_words)
                    else None
                )

                with st.spinner("Summarizing..."):
                    result = summarize_file_for_exam(
                        tmp_path,
                        length=length_map[length_ui],
                        target_words_override=override,
                    )

                if not result.ok:
                    st.error(f"Failed: {result.reason}")
                else:
                    direction = detect_direction(result.summary_md)
                    dir_class = "rtl" if direction == "rtl" else "ltr"

                    st.success("Done ✅")

                    st.write(
                        f"Chars: {result.char_count} | "
                        f"Tokens: {result.input_tokens} | "
                        f"Chunking: {result.used_chunking} | "
                        f"Chunks: {result.chunks_count} | "
                        f"Words: {result.actual_words}/{result.target_words}"
                    )

                    tab_preview, tab_export = st.tabs(["👀 Preview", "📋 Copy / Export"])

                    with tab_preview:
                        st.markdown(
                            f"""
                            <div class="card {dir_class}">
                            {result.summary_md}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    with tab_export:
                        st.text_area(
                            "Raw summary (Markdown)",
                            value=result.summary_md,
                            height=320,
                            key="raw_summary_md",
                        )

                        st.download_button(
                            "⬇️ Download summary.md",
                            data=result.summary_md.encode("utf-8"),
                            file_name="summary.md",
                            mime="text/markdown",
                            key="download_summary_md",
                        )

                        st.markdown(
                            "<div class='small-note'>Tip: Select All (⌘A) then Copy (⌘C).</div>",
                            unsafe_allow_html=True,
                        )

            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass