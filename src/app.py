# -*- coding: utf-8 -*-
"""
KanGen — Streamlit Frontend
Interactive web dashboard for the kanji flashcard pipeline.
"""
import os
import sys
import tempfile
import cv2 as cv
import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

# ── Path setup ───────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from internal.image_processing import (
    convert_heic_to_jpeg,
    load_image,
    find_table_contour,
    warp_perspective,
)
from internal.ocr import SmartOCRService
from internal.grouper import KanjiGrouper
from internal.llm import SmartEnhancer
from internal.anki import AnkiGenerator

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="漢 KanGen",
    page_icon="漢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+JP:wght@300;400;500;700&display=swap');

:root {
    --accent: #6C63FF;
    --accent-light: #8B83FF;
    --accent-glow: rgba(108, 99, 255, 0.25);
    --surface: #1A1B2E;
    --surface-alt: #232440;
    --card-bg: #282A45;
    --text: #E8E8F0;
    --text-dim: #9D9DB8;
    --success: #4ADE80;
    --warning: #FBBF24;
    --danger: #F87171;
}

/* Global */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', 'Noto Sans JP', sans-serif;
}

/* Hide default Streamlit elements */
#MainMenu, footer, header {visibility: hidden;}

/* Hero header */
.hero {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
}
.hero h1 {
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(135deg, #6C63FF 0%, #B794F6 50%, #6C63FF 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 3s linear infinite;
    margin-bottom: 0.2rem;
}
@keyframes shimmer {
    to { background-position: 200% center; }
}
.hero p {
    color: var(--text-dim);
    font-size: 1rem;
    font-weight: 300;
}

/* Stat cards */
.stat-row {
    display: flex;
    gap: 0.75rem;
    margin: 0.75rem 0;
}
.stat-card {
    flex: 1;
    background: var(--card-bg);
    border: 1px solid rgba(108, 99, 255, 0.15);
    border-radius: 12px;
    padding: 0.9rem 1rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px var(--accent-glow);
}
.stat-card .num {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--accent-light);
}
.stat-card .label {
    font-size: 0.75rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Tab styling */
[data-testid="stTabs"] button {
    font-weight: 500;
    font-size: 0.9rem;
}

/* Sidebar tweaks */
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(108,99,255,0.1);
}
[data-testid="stSidebar"] h2 {
    font-size: 1.1rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    api_key = st.text_input(
        "Gemini API Key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Optional — enables AI-enhanced meanings and examples",
    )
    use_gpu = st.toggle("Use GPU (CUDA)", value=False, help="Requires CUDA-compatible GPU")
    proximity = st.slider(
        "Proximity radius (px)",
        min_value=50,
        max_value=300,
        value=100,
        step=10,
        help="How far to search around each kanji anchor for associated text",
    )
    skip_warp = st.checkbox("Skip perspective correction", value=False)

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:var(--text-dim);font-size:0.75rem;'>"
        "漢 KanGen v2.0<br>Dictionary-first flashcards</div>",
        unsafe_allow_html=True,
    )


# ── Helpers ──────────────────────────────────────────────────────────────
def cv_to_rgb(img: np.ndarray) -> np.ndarray:
    """Convert OpenCV BGR image to RGB for Streamlit display."""
    return cv.cvtColor(img, cv.COLOR_BGR2RGB)


def draw_contour_overlay(image: np.ndarray, contour: np.ndarray) -> np.ndarray:
    """Draw a green contour on a copy of the image."""
    vis = image.copy()
    cv.drawContours(vis, [contour], -1, (0, 255, 0), 3)
    return vis


@st.cache_resource(show_spinner="Loading OCR engine…")
def get_ocr_service(gpu: bool) -> SmartOCRService:
    """Cache the heavy EasyOCR model across reruns."""
    return SmartOCRService(use_gpu=gpu)


# ── Session state init ───────────────────────────────────────────────────
for key in ("text_blocks", "cards_df", "debug_contour", "debug_warped",
            "original_img", "processed", "deck_bytes"):
    if key not in st.session_state:
        st.session_state[key] = None


# ── Main area ────────────────────────────────────────────────────────────
st.markdown(
    '<div class="hero">'
    '<h1>漢 KanGen</h1>'
    '<p>Upload a kanji study image → review → download your Anki deck</p>'
    '</div>',
    unsafe_allow_html=True,
)

uploaded = st.file_uploader(
    "Drop your study image here",
    type=["jpg", "jpeg", "png", "heic", "heif"],
    help="Supports JPEG, PNG, HEIC/HEIF",
)

if uploaded is not None:
    # Save to temp file so OpenCV can read it
    suffix = Path(uploaded.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.getvalue())
    tmp.flush()
    tmp_path = Path(tmp.name)

    # Show small preview
    with st.expander("📷 Uploaded image preview", expanded=False):
        st.image(uploaded, use_container_width=True)

    # ── Generate button ──────────────────────────────────────────────
    if st.button("🚀 Generate Deck", type="primary", use_container_width=True):
        progress = st.progress(0, text="Initializing…")

        try:
            # Step 1 — Image preprocessing (10%)
            progress.progress(5, text="Loading image…")
            img_path = convert_heic_to_jpeg(tmp_path)
            original_img = load_image(img_path)
            st.session_state.original_img = original_img

            contour_overlay = None
            if not skip_warp:
                progress.progress(10, text="Detecting table contour…")
                table_contour = find_table_contour(original_img)
                if table_contour is not None:
                    contour_overlay = draw_contour_overlay(original_img, table_contour)
                    processed_img = warp_perspective(original_img, table_contour)
                else:
                    st.toast("⚠️ No table contour found — using full image", icon="⚠️")
                    processed_img = original_img
            else:
                processed_img = original_img

            st.session_state.debug_contour = contour_overlay
            st.session_state.debug_warped = processed_img

            # Step 2 — OCR (30%)
            progress.progress(20, text="Running OCR…")
            ocr_service = get_ocr_service(use_gpu)
            text_blocks = ocr_service.extract_all_text_with_context(processed_img)

            if not text_blocks:
                st.error("No text detected in image.")
                progress.empty()
                st.stop()

            st.session_state.text_blocks = text_blocks
            progress.progress(40, text=f"Detected {len(text_blocks)} text blocks")

            # Step 3 — Grouping (50%)
            progress.progress(50, text="Grouping kanji entries…")
            grouper = KanjiGrouper(proximity_radius=proximity)
            kanji_entries = grouper.group_by_proximity(text_blocks)

            if not kanji_entries:
                st.error("No kanji entries found.")
                progress.empty()
                st.stop()

            progress.progress(60, text=f"Found {len(kanji_entries)} kanji entries")

            # Step 4 — Enhancement (60-90%)
            progress.progress(65, text="Enhancing with AI + dictionary…")
            enhancer = SmartEnhancer(api_key=api_key if api_key else None)
            cards = enhancer.enhance_all(kanji_entries)

            progress.progress(90, text="Building flashcard table…")

            # Build editable dataframe
            rows = []
            for card in cards:
                rows.append({
                    "Kanji": card.kanji,
                    "Meaning": card.meaning,
                    "On-yomi": card.on_yomi,
                    "Kun-yomi": card.kun_yomi,
                    "Example": card.example,
                })

            st.session_state.cards_df = pd.DataFrame(rows)
            st.session_state.deck_bytes = None  # reset download

            progress.progress(100, text="✅ Done!")

        except Exception as e:
            st.error(f"Pipeline error: {e}")
            progress.empty()

    # ── Tabs ─────────────────────────────────────────────────────────
    if st.session_state.cards_df is not None or st.session_state.text_blocks is not None:
        # Stat bar
        n_blocks = len(st.session_state.text_blocks) if st.session_state.text_blocks else 0
        n_cards = len(st.session_state.cards_df) if st.session_state.cards_df is not None else 0
        st.markdown(
            f'<div class="stat-row">'
            f'<div class="stat-card"><div class="num">{n_blocks}</div><div class="label">Text Blocks</div></div>'
            f'<div class="stat-card"><div class="num">{n_cards}</div><div class="label">Cards</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        tab_debug, tab_ocr, tab_cards = st.tabs(["🔍 Visual Debug", "📝 Raw OCR", "📇 Flashcards"])

        # ── Tab 1: Visual Debug ──────────────────────────────────────
        with tab_debug:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Original + contour**")
                if st.session_state.debug_contour is not None:
                    st.image(cv_to_rgb(st.session_state.debug_contour), use_container_width=True)
                elif st.session_state.original_img is not None:
                    st.image(cv_to_rgb(st.session_state.original_img), use_container_width=True,
                             caption="No contour detected")
                else:
                    st.info("Run the pipeline first.")
            with col2:
                st.markdown("**Perspective-corrected**")
                if st.session_state.debug_warped is not None:
                    st.image(cv_to_rgb(st.session_state.debug_warped), use_container_width=True)
                else:
                    st.info("Run the pipeline first.")

        # ── Tab 2: Raw OCR ───────────────────────────────────────────
        with tab_ocr:
            if st.session_state.text_blocks:
                ocr_rows = []
                for b in st.session_state.text_blocks:
                    ocr_rows.append({
                        "Text": b.text,
                        "Confidence": round(b.confidence, 3),
                        "Kanji?": "✅" if b.is_kanji else "",
                        "Kana?": "✅" if b.is_kana else "",
                        "Latin?": "✅" if b.is_latin else "",
                        "Center X": round(b.center[0], 1),
                        "Center Y": round(b.center[1], 1),
                    })
                st.dataframe(
                    pd.DataFrame(ocr_rows),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Run the pipeline to see OCR results.")

        # ── Tab 3: Flashcards ────────────────────────────────────────
        with tab_cards:
            if st.session_state.cards_df is not None and not st.session_state.cards_df.empty:
                st.markdown("Edit any cell below before downloading:")
                edited_df = st.data_editor(
                    st.session_state.cards_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    hide_index=True,
                    key="cards_editor",
                )

                st.markdown("---")

                # ── Download ─────────────────────────────────────────
                if st.button("📥 Build & Download .apkg", use_container_width=True):
                    with st.spinner("Building Anki deck…"):
                        gen = AnkiGenerator()
                        for _, row in edited_df.iterrows():
                            gen.add_card(
                                str(row.get("Kanji", "")),
                                str(row.get("Meaning", "")),
                                str(row.get("On-yomi", "")),
                                str(row.get("Kun-yomi", "")),
                                str(row.get("Example", "")),
                            )

                        stats = gen.get_statistics()
                        if stats["created"] == 0:
                            st.warning("No valid cards to export.")
                        else:
                            # Write to temp file, then read bytes for download
                            with tempfile.NamedTemporaryFile(suffix=".apkg", delete=False) as f:
                                out_path = Path(f.name)
                            gen.save_package(out_path)
                            st.session_state.deck_bytes = out_path.read_bytes()
                            st.success(
                                f"Deck built — **{stats['created']}** cards created, "
                                f"**{stats['skipped']}** skipped"
                            )

                if st.session_state.deck_bytes:
                    st.download_button(
                        label="⬇️ Download output_deck.apkg",
                        data=st.session_state.deck_bytes,
                        file_name="output_deck.apkg",
                        mime="application/octet-stream",
                        use_container_width=True,
                        type="primary",
                    )
            else:
                st.info("Run the pipeline to generate flashcards.")

else:
    # No file uploaded — show instructions
    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem; color: var(--text-dim);">
        <p style="font-size: 3rem; margin-bottom: 0.5rem;">📸</p>
        <p style="font-size: 1.1rem;">Upload a photo of your kanji study sheet to get started.</p>
        <p style="font-size: 0.85rem;">Supported: JPEG, PNG, HEIC</p>
    </div>
    """, unsafe_allow_html=True)
