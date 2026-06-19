import streamlit as st
from markitdown import MarkItDown
import os
import time
import io
import zipfile
import re

st.set_page_config(
    page_title="DocFlow — Document to Markdown Converter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# THEME (Light, with optional dark toggle)
# ============================================================
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: name, words, chars, size, time, content

def inject_css(theme: str):
    if theme == "light":
        bg, card, text, subtext, border = "#f7f8fb", "#ffffff", "#111827", "#6b7280", "#e5e7eb"
        accent1, accent2 = "#4f46e5", "#db2777"
        pill_bg, pill_border, pill_text = "rgba(79,70,229,0.08)", "rgba(79,70,229,0.25)", "#4338ca"
    else:
        bg, card, text, subtext, border = "#0e1117", "#161b22", "#f3f4f6", "#9ca3af", "rgba(255,255,255,0.08)"
        accent1, accent2 = "#818cf8", "#f472b6"
        pill_bg, pill_border, pill_text = "rgba(99,102,241,0.15)", "rgba(99,102,241,0.4)", "#c7d2fe"

    st.markdown(f"""
    <style>
        .stApp {{ background-color: {bg}; color: {text}; }}
        [data-testid="stSidebar"] {{ background-color: {card}; border-right: 1px solid {border}; }}

        .hero {{ text-align: center; padding: 2rem 0 0.5rem 0; }}
        .hero h1 {{
            font-size: 2.8rem; font-weight: 800; margin-bottom: 0.3rem;
            background: linear-gradient(90deg, {accent1}, {accent2});
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        .hero p {{ color: {subtext}; font-size: 1.15rem; margin-top: 0; max-width: 640px; margin-left:auto; margin-right:auto; }}

        .format-pill {{
            display: inline-block; padding: 5px 14px; margin: 4px;
            border-radius: 999px; background: {pill_bg}; border: 1px solid {pill_border};
            color: {pill_text}; font-size: 0.8rem; font-weight: 600;
        }}

        .feature-card {{
            background: {card}; border: 1px solid {border}; border-radius: 16px;
            padding: 1.3rem; height: 100%;
        }}
        .feature-card h4 {{ margin: 0.3rem 0 0.4rem 0; color: {text}; }}
        .feature-card p {{ color: {subtext}; font-size: 0.88rem; margin: 0; }}
        .feature-icon {{ font-size: 1.6rem; }}

        .usecase-card {{
            background: {card}; border-left: 4px solid {accent1}; border-radius: 10px;
            padding: 0.9rem 1.1rem; margin-bottom: 0.6rem;
        }}
        .usecase-card b {{ color: {text}; }}
        .usecase-card span {{ color: {subtext}; font-size: 0.85rem; }}

        div[data-testid="stFileUploader"] {{
            border: 2px dashed {accent1}55; border-radius: 14px;
            padding: 1.2rem; background: {card};
        }}

        .stat-card {{
            background: {card}; border: 1px solid {border}; border-radius: 12px;
            padding: 0.9rem; text-align: center;
        }}
        .stat-card h3 {{ margin: 0; font-size: 1.5rem; color: {accent1}; }}
        .stat-card p {{ margin: 0; color: {subtext}; font-size: 0.78rem; }}

        .stButton button, .stDownloadButton button {{
            border-radius: 10px; font-weight: 600;
        }}

        .section-title {{
            font-size: 1.4rem; font-weight: 700; margin: 1.6rem 0 0.8rem 0; color: {text};
        }}

        footer {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

inject_css(st.session_state.theme)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    theme_choice = st.toggle("🌙 Dark mode", value=(st.session_state.theme == "dark"))
    new_theme = "dark" if theme_choice else "light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    st.markdown("---")
    st.markdown("### 📤 Export options")
    export_formats = st.multiselect(
        "Output formats", ["Markdown (.md)", "Plain text (.txt)", "HTML (.html)"],
        default=["Markdown (.md)"]
    )
    max_size_mb = st.slider("Max file size (MB)", 1, 200, 25)

    st.markdown("---")
    st.markdown("### 🕓 Session history")
    if st.session_state.history:
        for h in reversed(st.session_state.history[-8:]):
            st.caption(f"📄 {h['name']} — {h['words']:,} words")
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No conversions yet this session.")

# ============================================================
# HERO / LANDING SECTION
# ============================================================
st.markdown("""
<div class="hero">
    <h1>📄 DocFlow</h1>
    <p>Convert PDFs, Word docs, spreadsheets, presentations and more into clean,
    token-efficient Markdown — perfect for feeding into LLMs, search indexes, or note systems.</p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div style="text-align:center; margin-bottom:1rem;">'
    + "".join(f'<span class="format-pill">{f}</span>' for f in
              ["PDF", "DOCX", "XLSX", "PPTX", "CSV", "JSON", "XML", "TXT", "URL / Web page"])
    + '</div>', unsafe_allow_html=True
)

c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    st.markdown("<div style='text-align:center; margin-bottom:1.2rem;'>", unsafe_allow_html=True)
    jump = st.button("🚀 Start Converting", use_container_width=True, type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Features ----------
st.markdown('<div class="section-title">✨ Why DocFlow</div>', unsafe_allow_html=True)
features = [
    ("⚡", "Fast & Local", "Conversion runs instantly, no documents leave your session longer than needed."),
    ("🧠", "LLM-Ready Output", "Clean Markdown structure that's optimized for token efficiency in AI pipelines."),
    ("📦", "Batch Processing", "Upload multiple files and download everything as a single zip archive."),
    ("✏️", "Editable Output", "Tweak the generated Markdown right in the browser before exporting."),
    ("🌐", "URL Conversion", "Paste a web page or PDF link to convert it without downloading first."),
    ("🔍", "OCR Awareness", "Flags when scanned PDFs or images required OCR text extraction."),
]
cols = st.columns(3)
for i, (icon, title, desc) in enumerate(features):
    with cols[i % 3]:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <h4>{title}</h4>
            <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)
    if i % 3 == 2:
        st.write("")

st.write("")

# ---------- Use cases ----------
st.markdown('<div class="section-title">💡 Who uses this</div>', unsafe_allow_html=True)
use_cases = [
    ("AI / RAG pipelines", "Convert source documents into Markdown chunks before embedding."),
    ("Researchers & students", "Turn PDFs and slide decks into searchable, editable notes."),
    ("Technical writers", "Migrate legacy Word/PowerPoint content into Markdown-based docs."),
    ("Data teams", "Quickly inspect spreadsheet contents as structured, readable text."),
]
uc_cols = st.columns(2)
for i, (title, desc) in enumerate(use_cases):
    with uc_cols[i % 2]:
        st.markdown(f"""
        <div class="usecase-card">
            <b>{title}</b><br><span>{desc}</span>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ============================================================
# CONVERTER SECTION
# ============================================================
st.markdown('<div class="section-title">📥 Convert your files</div>', unsafe_allow_html=True)

tab_upload, tab_url = st.tabs(["📁 Upload files", "🌐 Convert from URL"])

def estimate_tokens(text: str) -> int:
    # Rough heuristic: ~4 characters per token (average for English)
    return max(1, len(text) // 4)

def detect_ocr_likely(filename: str, text: str) -> bool:
    if filename.lower().endswith(".pdf"):
        if len(text.strip()) < 200:
            return True
    return False

def build_outputs(text_content: str, base_name: str, formats: list):
    outputs = {}
    if "Markdown (.md)" in formats:
        outputs[f"{base_name}.md"] = text_content
    if "Plain text (.txt)" in formats:
        plain = re.sub(r"[#*_`>\-]{1,3}", "", text_content)
        outputs[f"{base_name}.txt"] = plain
    if "HTML (.html)" in formats:
        try:
            import markdown as md_lib
            html = md_lib.markdown(text_content, extensions=["tables", "fenced_code"])
        except ImportError:
            html = f"<pre>{text_content}</pre>"
        outputs[f"{base_name}.html"] = f"<html><body>{html}</body></html>"
    return outputs

def render_result(name: str, text_content: str, size_bytes: int, elapsed: float):
    word_count = len(text_content.split())
    char_count = len(text_content)
    token_est = estimate_tokens(text_content)
    base_name = os.path.splitext(name)[0]

    st.markdown(f"#### 📑 {name}")
    st.success(f"✅ Converted in {elapsed:.2f}s")

    if detect_ocr_likely(name, text_content):
        st.warning("⚠️ Very little extractable text found — this file may be a scanned/image-based PDF requiring OCR for full accuracy.")

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in zip(
        [c1, c2, c3, c4],
        [f"{word_count:,}", f"{char_count:,}", f"{size_bytes/1024:,.1f} KB", f"~{token_est:,}"],
        ["Words", "Characters", "Original Size", "Est. Tokens"]
    ):
        with col:
            st.markdown(f'<div class="stat-card"><h3>{val}</h3><p>{label}</p></div>', unsafe_allow_html=True)

    st.write("")
    edited_text = st.text_area(
        "✏️ Edit Markdown before exporting",
        value=text_content, height=260, key=f"edit_{name}"
    )

    with st.expander("👀 Rendered preview"):
        st.markdown(edited_text)

    outputs = build_outputs(edited_text, base_name, export_formats or ["Markdown (.md)"])

    dl_cols = st.columns(len(outputs) if outputs else 1)
    for i, (fname, content) in enumerate(outputs.items()):
        mime = "text/markdown" if fname.endswith(".md") else ("text/html" if fname.endswith(".html") else "text/plain")
        with dl_cols[i]:
            st.download_button(f"📥 {fname}", data=content, file_name=fname, mime=mime, key=f"dl_{fname}_{name}")

    st.session_state.history.append({
        "name": name, "words": word_count, "chars": char_count,
        "size": size_bytes, "time": elapsed, "outputs": outputs
    })
    return outputs

all_zip_outputs = {}

with tab_upload:
    uploaded_files = st.file_uploader(
        "Drop your file(s) here, or click to browse",
        type=["pdf", "docx", "xlsx", "xls", "pptx", "txt", "csv", "json", "xml"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.size > max_size_mb * 1024 * 1024:
                st.error(f"❌ {uploaded_file.name} exceeds the {max_size_mb} MB limit set in the sidebar.")
                continue

            temp_filename = uploaded_file.name
            with open(temp_filename, "wb") as f:
                f.write(uploaded_file.getbuffer())

            start = time.time()
            with st.spinner(f"Converting {uploaded_file.name} ..."):
                try:
                    md = MarkItDown()
                    result = md.convert(temp_filename)
                    elapsed = time.time() - start
                    outputs = render_result(uploaded_file.name, result.text_content, uploaded_file.size, elapsed)
                    all_zip_outputs.update(outputs)
                except Exception as e:
                    st.error(f"An error occurred during conversion of {uploaded_file.name}: {e}")
                finally:
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
            st.divider()

        if all_zip_outputs and len(uploaded_files) > 1:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for fname, content in all_zip_outputs.items():
                    zf.writestr(fname, content)
            zip_buffer.seek(0)
            st.markdown('<div class="section-title">📦 Batch download</div>', unsafe_allow_html=True)
            st.download_button(
                "📦 Download all as .zip",
                data=zip_buffer,
                file_name="converted_files.zip",
                mime="application/zip",
                use_container_width=True,
            )
    else:
        st.info("👆 Upload one or more files to get started. Multiple files are supported.")

with tab_url:
    url_input = st.text_input("Paste a web page or PDF URL", placeholder="https://example.com/article")
    if st.button("Convert URL", type="primary"):
        if not url_input.strip():
            st.warning("Please enter a URL first.")
        else:
            start = time.time()
            with st.spinner(f"Fetching and converting {url_input} ..."):
                try:
                    md = MarkItDown()
                    result = md.convert(url_input)
                    elapsed = time.time() - start
                    safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", url_input)[:50] or "webpage"
                    render_result(f"{safe_name}.url", result.text_content, len(result.text_content.encode("utf-8")), elapsed)
                except Exception as e:
                    st.error(f"Could not convert that URL: {e}")

st.divider()
st.caption("Built by <strong>Mohit Kumar</strong>. DocFlow turns any document into clean Markdown, ready for humans or AI.", unsafe_allow_html=True)
