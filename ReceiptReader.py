import streamlit as st
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, Tk
import streamlit as st
import os, json, shutil, tempfile, zipfile
from pathlib import Path
from tkinter import filedialog, Tk
from dotenv import dotenv_values    

#config
st.set_page_config(page_title="OCR Receipt Reader", layout="wide")
st.title("🧾 OCR Receipt Reader")

PROJECT_DIR = Path(__file__).parent          # folder that holds .env + ui.py
ENV_PATH    = PROJECT_DIR / ".env"
KEY_ENV     = "OPENAI_API_KEY"

KEY_ENV   = "OPENAI_API_KEY"
GCV_ENV   = "GOOGLE_APPLICATION_CREDENTIALS"

# ───────────────────────── key validators ──────────────────────────────
def openai_key_in_file() -> bool:
    """True iff .env holds a valid sk‑ key."""
    key = dotenv_values(ENV_PATH).get(KEY_ENV)
    return bool(key and key.startswith("sk-"))

def gcv_key_in_file() -> bool:
    """True iff .env points to a valid service‑account JSON file."""
    path = dotenv_values(ENV_PATH).get(GCV_ENV)
    if not path:
        return False
    p = Path(path)
    if not p.is_file():
        return False
    try:
        data = json.loads(p.read_text())
        return data.get("type") == "service_account" and "private_key" in data
    except Exception:
        return False

# ───────────────────────── gatekeeper ──────────────────────────────────
if not (openai_key_in_file() and gcv_key_in_file()):
    st.warning(
        "Required API keys not found in `.env`.\n\n"
        "Configure them first via **“🔑 Configure API keys”** in the sidebar."
    )
    st.stop()

# helpers
VALID_EXT    = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
PURIFIED_DIR = Path("images_purified")

def get_downloads_folder() -> Path:
    return (Path(os.environ.get("USERPROFILE", "")) / "Downloads"
            if os.name == "nt" else Path.home() / "Downloads")

def pick_directory() -> str | None:
    try:
        root: Tk = tk.Tk()
        root.attributes("-topmost", True)
        root.withdraw()
        folder = filedialog.askdirectory()
        root.destroy()
        return folder or None
    except Exception:
        return None

# session state 
DEFAULTS = {
    "temp_dir": Path(tempfile.mkdtemp(prefix="receipt_uploads_")),
    "images": {},
    "folder_selected": None,
    "zip_saved": False,
    "uploader_key": 0,
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

#success
if st.session_state.zip_saved:
    st.toast("✅ images_purified.zip saved to Downloads", icon="📁")
    st.session_state.zip_saved = False

# controls
st.subheader("📤 Upload receipts")

if st.button("📂  Select folder"):
    picked = pick_directory()
    if picked:
        st.session_state.images = {
            p.name: p for p in Path(picked).iterdir()
            if p.suffix.lower() in VALID_EXT
        }
        st.session_state.folder_selected = picked
        shutil.rmtree(st.session_state.temp_dir, ignore_errors=True)
        st.session_state.temp_dir = Path(tempfile.mkdtemp(prefix="receipt_uploads_"))
        st.session_state.uploader_key += 1
        st.rerun()

col_up, col_btn = st.columns([4, 1])
with col_up:
    uploaded_files = st.file_uploader(
        "Drag & drop images here or click Browse",
        type=list(VALID_EXT),
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed",
    )

# clear images in memory
if uploaded_files is None and st.session_state.folder_selected is None:
    for path in st.session_state.images.values():
        if path.parent == st.session_state.temp_dir:
            path.unlink(missing_ok=True)
    st.session_state.images.clear()

if uploaded_files is not None:
    current = {uf.name for uf in uploaded_files}   
    # remove unchecked
    for name in list(st.session_state.images):
        if name not in current:
            path = st.session_state.images.pop(name)
            if path.parent == st.session_state.temp_dir:
                path.unlink(missing_ok=True)
    # add new
    for uf in uploaded_files:
        if uf.name in st.session_state.images:
            continue
        dest = st.session_state.temp_dir / uf.name
        base, ext = os.path.splitext(dest.name)
        ctr = 1
        while dest.exists():
            dest = dest.with_name(f"{base}_{ctr}{ext}")
            ctr += 1
        dest.write_bytes(uf.getbuffer())
        st.session_state.images[uf.name] = dest
    st.session_state.folder_selected = None

# process images btn
with col_btn:
    run_clicked = st.button(
        "⚙️  Process & Download",
        disabled=not st.session_state.images,
    )

### MAIN ###

if run_clicked:
    # temp list of paths chosen by the user
    img_paths = list(st.session_state.images.values())
    total = len(img_paths)
    if total == 0:
        st.warning("No images selected")
        st.stop()

    # 1️⃣  Purify ------------------------------------------------------------
    shutil.rmtree(PURIFIED_DIR, ignore_errors=True)
    PURIFIED_DIR.mkdir(parents=True, exist_ok=True)

    progress = st.progress(0.0, text=f"Purifying… 0 / {total}")
    done = 0
    for path in img_paths:
        if os.system(f'python purifier.py "{path}"') != 0:
            st.error(f"Purifier failed on {path.name}")
            st.stop()
        done += 1
        progress.progress(done / total, text=f"Purifying… {done} / {total}")
    progress.empty()

    # 2️⃣  OCR each cleaned image ------------------------------------------
    EXTRACT_DIR = Path("ocr_extractions")
    shutil.rmtree(EXTRACT_DIR, ignore_errors=True)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    cleaned_imgs = [p for p in PURIFIED_DIR.iterdir() if p.suffix.lower() in VALID_EXT]
    total_ocr = len(cleaned_imgs)
    progress = st.progress(0.0, text=f"OCR… 0 / {total_ocr}")
    done = 0
    for img in cleaned_imgs:
        if os.system(f'python ocrengine.py "{img}"') != 0:
            st.error(f"OCR failed on {img.name}")
            st.stop()
        done += 1
        progress.progress(done / total_ocr, text=f"OCR… {done} / {total_ocr}")
    progress.empty()

    # 3️⃣  Combine individual CSVs -----------------------------------------
    import pandas as pd
    csv_files = list(EXTRACT_DIR.glob("*.csv"))
    if not csv_files:
        st.error("No OCR extractions found.")
        st.stop()

    combined_df = pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)
    combined_path = get_downloads_folder() / "receipt_extractions.csv"
    combined_df.to_csv(combined_path, index=False)
        
    # 🔔 toast letting the user know where it was saved
    st.toast("✅ receipt_extractions.csv saved to Downloads", icon="📁")

    # 🚮  delete the individual extraction CSVs ------------------------------
    for f in csv_files:
        f.unlink(missing_ok=True)

    # 4️⃣  Download button ---------------------------------------------------
    download_clicked = st.download_button(
        "📥 Download combined CSV",
        open(combined_path, "rb"),
        file_name="receipt_extractions.csv",
        mime="text/csv",
    )

    # 5️⃣  Reset session (only after download clicked) ----------------------
    if download_clicked:
        # remove temp folders & clear images
        shutil.rmtree(st.session_state.temp_dir, ignore_errors=True)
        st.session_state.update({
            "temp_dir": Path(tempfile.mkdtemp(prefix="receipt_uploads_")),
            "images": {},
            "folder_selected": None,
            "uploader_key": st.session_state.uploader_key + 1,
        })
        st.rerun()

# selected images preview
if st.session_state.images:
    st.write("### Selected images")
    cols_per_row = 4
    for idx, (name, p) in enumerate(st.session_state.images.items()):
        if idx % cols_per_row == 0:
            cols = st.columns(cols_per_row)
        with cols[idx % cols_per_row]:
            try:
                st.image(p.open("rb").read(), caption=name, width=180)
            except Exception:
                st.warning(f"Cannot preview {name}")
