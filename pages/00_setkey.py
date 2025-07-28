import streamlit as st
import os, json
from pathlib import Path
from dotenv import load_dotenv, set_key, dotenv_values

# ─────────────────── paths / consts ────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent.parent          # root of the repo
ENV_PATH    = PROJECT_DIR / ".env"
OA_ENV      = "OPENAI_API_KEY"
GCV_ENV     = "GOOGLE_APPLICATION_CREDENTIALS"

# ─────────────────── helpers ───────────────────────────────────────────────
def oa_key_valid(key: str | None) -> bool:
    return bool(key and key.startswith("sk-"))

def gcv_key_valid(path_str: str | None) -> bool:
    if not path_str:
        return False
    p = Path(path_str)
    if not p.is_file():
        return False
    try:
        data = json.loads(p.read_text())
        return data.get("type") == "service_account" and "private_key" in data
    except Exception:
        return False

# ─────────────────── load current .env values (file only) ──────────────────
env_vals     = dotenv_values(ENV_PATH)
current_oa   = env_vals.get(OA_ENV)
current_gcv  = env_vals.get(GCV_ENV)

oa_ok  = oa_key_valid(current_oa)
gcv_ok = gcv_key_valid(current_gcv)

# ─────────────────── page layout ───────────────────────────────────────────
st.set_page_config(page_title="Configure API keys", layout="centered")
st.title("🔑 Configure API keys")

st.markdown(
    """
    This application needs **two** keys stored locally in `.env`:

    1. **OpenAI API key** – starts with `sk‑…` (used for receipt parsing)  
    2. **Google Vision service‑account JSON** – `*.json` file (used for OCR)

    Keys are saved **only on your computer** and never uploaded anywhere.
    """
)

# ─────────────────── if both keys valid → done ─────────────────────────────
if oa_ok and gcv_ok:
    st.success("✅ Both OpenAI and Google Vision keys are configured.")
    st.write("You can continue using the sidebar ➡️")
    st.stop()

# ─────────────────── OpenAI key form (if needed) ───────────────────────────
if not oa_ok:
    st.subheader("1️⃣ OpenAI API key")
    with st.form("oa_form", clear_on_submit=True):
        new_oa = st.text_input("Paste your OpenAI key (starts with `sk-…`)",
                               type="password")
        oa_ack = st.checkbox("I understand this key is stored locally.")
        oa_sub = st.form_submit_button("Save OpenAI key")

    if oa_sub:
        if not oa_key_valid(new_oa):
            st.error("That doesn’t look like a valid `sk-…` key.")
            st.stop()
        if not oa_ack:
            st.error("Please acknowledge local storage.")
            st.stop()
        ENV_PATH.touch(exist_ok=True)
        set_key(str(ENV_PATH), OA_ENV, new_oa)
        os.environ[OA_ENV] = new_oa
        st.success("✅ OpenAI key saved.")
        st.rerun()

# ─────────────────── Google Vision key upload (if needed) ──────────────────
if not gcv_ok:
    st.subheader("2️⃣ Google Vision service‑account JSON")
    gcv_file = st.file_uploader(
        "Upload your `*.json` key file",
        type=["json"],
        accept_multiple_files=False,
        key="gcv_uploader",
    )

    if gcv_file is not None:
        tmp_path = PROJECT_DIR / gcv_file.name
        tmp_path.write_bytes(gcv_file.getbuffer())

        if not gcv_key_valid(str(tmp_path)):
            tmp_path.unlink(missing_ok=True)
            st.error("❌ That file is not a valid service‑account JSON.")
            st.stop()

        ENV_PATH.touch(exist_ok=True)
        set_key(str(ENV_PATH), GCV_ENV, str(tmp_path))
        os.environ[GCV_ENV] = str(tmp_path)
        st.success("✅ Google Vision key saved.")
        st.rerun()
