#!/usr/bin/env python3
"""
ocrengine.py – Google Vision OCR ➜ GPT parse ➜ save 1‑row CSV

Called by receiptreader.py with:
    os.system(f'python ocrengine.py "{purified_img_path}"')

Side‑effect:
    ocr_extractions/<image_stem>.csv
"""

import os, sys, csv, json, re, logging, traceback
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from google.cloud import vision
from openai import OpenAI

# ────────────────────────── ENV & CLIENTS ──────────────────────────────────
load_dotenv(find_dotenv())

# ❶ Google Vision key
gcv_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not gcv_key or not Path(gcv_key).is_file():
    raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS missing / invalid")
gcv_client = vision.ImageAnnotatorClient.from_service_account_file(gcv_key)

# ❷ OpenAI key
openai_key = os.getenv("OPENAI_API_KEY", "")
if not openai_key.startswith("sk-"):
    raise RuntimeError("OPENAI_API_KEY missing / invalid")
oa_client = OpenAI(api_key=openai_key)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# output folder that receiptreader later concatenates
EXTRACT_DIR = Path("ocr_extractions")
EXTRACT_DIR.mkdir(exist_ok=True)

# ────────────────────────── OPENAI PROMPT PARSER ───────────────────────────
def parse_receipt_with_gpt(text: str) -> dict:
    prompt = f"""
You are a receipt parser. Extract these fields from the text below:

- merchant
- item
- amount (if total amount is available on the receipt, equate it to this. Otherwise get the total sum of all items in the receipt)
- date (as ISO format: YYYY-MM-DD)

Read the receipt text, apply contextual analysis, leave missing fields null.
Return **only** JSON with keys: merchant, item, amount, date.

Receipt:
{text}
"""
    rsp = oa_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    raw = rsp.choices[0].message.content.strip()

    # keep just the first {...} block so extra prose doesn't break JSON
    m = re.search(r"\{.*\}", raw, re.S)
    cleaned = m.group(0) if m else raw
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logging.warning("GPT invalid JSON – saving nulls\n%s", raw)
        return {"merchant": None, "date": None, "item": None, "amount": None}

# ────────────────────────── GCV OCR ────────────────────────────────────────
def ocr_image(img_path: Path) -> str:
    content = img_path.read_bytes()
    resp = gcv_client.document_text_detection(image=vision.Image(content=content))
    if resp.error.message:
        raise RuntimeError(resp.error.message)
    return resp.full_text_annotation.text or ""

# ────────────────────────── MAIN ROUTINE ───────────────────────────────────
def process_image(img: str | Path) -> None:
    p = Path(img)
    if not p.is_file():
        raise FileNotFoundError(p)

    print(f"OCR → {p.name}", flush=True)

    full_text = ocr_image(p)
    print(f"  · OCR chars      : {len(full_text)}", flush=True)

    parsed = parse_receipt_with_gpt(full_text)
    print(f"  · parsed JSON    : {parsed}", flush=True)

    csv_path = EXTRACT_DIR / f"{p.stem}.csv"
    try:
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["merchant", "date", "item", "amount"]
            )
            writer.writeheader()
            writer.writerow(parsed)
        print(f"✔ wrote CSV       : {csv_path}", flush=True)
    except Exception as e:
        print("❌ CSV write error :", e, flush=True)
        traceback.print_exc()

# ────────────────────────── CLI ENTRY ──────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ocrengine.py <cleaned_image_path>")
        sys.exit(1)
    process_image(sys.argv[1])
