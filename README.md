# CashOut

A combined Streamlit and CLI tool for OCR‑based receipt reading using Google Cloud Vision and OpenAI LLMs. Clean images, extract text, parse structured data, and export results as CSV.

---

## 📦 Project Structure

```text
├── ReceiptReader.py      # Streamlit front‑end UI for uploading, purifying, OCR, and downloading
├── purifier.py           # Image cleaning / pre‑processing script
├── OCRengine.py          # CLI tool to run Vision OCR and generate per‑receipt CSVs in `ocr_extractions/`
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables for API keys
├── .gitignore            # Files and folders to ignore in Git
├── images_purified/      # Output of purified images
├── ocr_extractions/      # Individual CSV outputs from OCRengine.py
├── pages/                # (Optional) Streamlit multipage extensions
└── README.md             # This documentation
```

---

## 🚀 Quick Start

1. **Clone the repo**

   ```bash
   git clone https://github.com/5kyDragonfly/CashOut.git
   cd CashOut
   ```

2. **Create and activate a Python virtual environment**

   ```bash
   python -m venv env
   # Windows
   env\Scripts\Activate
   # macOS/Linux
   source env/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure API keys**

   Create a `.env` file in the project root with the following entries:

   ```ini
   GOOGLE_APPLICATION_CREDENTIALS=./path/to/your‑gcv‑service‑account.json
   OPENAI_API_KEY=sk‑your_openai_key
   ```

   * Place the Google service‐account JSON at the specified path.

5. **Run the Streamlit app**

   ```bash
   streamlit run ReceiptReader.py
   ```

6. **Or use the CLI to OCR receipts directly**

   ```bash
   python OCRengine.py /path/to/cleaned_image.png
   ```

   This generates a CSV for each receipt under `ocr_extractions/`.

---

## 📝 Workflow Overview

1. **Image Cleaning** (`purifier.py`)
   Applies perspective correction, cropping, and contrast enhancements.

2. **Receive & Purify** (Streamlit)
   Upload or select folders of images; cleans and previews them in `images_purified/`.

3. **OCR Extraction** (`OCRengine.py`)
   Uses Google Cloud Vision’s `document_text_detection` to produce raw and filtered text dumps plus per‑receipt CSVs.

4. **LLM Parsing** (Optional extension)
   Send filtered text to OpenAI’s API to extract fields: `merchant`, `item`, `amount`, `date`.

5. **Download Results** (Streamlit)
   Combine all individual CSVs into a single `receipt_extractions.csv` and download via button.

---

## ⚙️ Configuration

| File/Env           | Purpose                                                                               |
| ------------------ | ------------------------------------------------------------------------------------- |
| `.env`             | API keys (`GOOGLE_APPLICATION_CREDENTIALS`, `OPENAI_API_KEY`)                         |
| `requirements.txt` | Lists Python libraries: streamlit, google‑cloud‑vision, openai, python‑dotenv, pandas |

Streamlit settings can be customized in `ReceiptReader.py` (page title, layout, etc.).

---

## 🔄 Extensibility

* **Batch CLI**: Add a `--directory` flag to `OCRengine.py` to process multiple images in one go.
* **Retry Logic**: Implement exponential backoff around Vision and OpenAI calls for resilience.
* **Alternate Models**: Swap `gpt‑4o‑mini` for other OpenAI models or fine‑tuned parsers.

---

## 📝 License

Skyvn S. Padayhag
Darrel Ethan Ong
