import sys
import logging
from pathlib import Path
import cv2
from PIL import Image
import numpy as np

# config
VALID_EXT   = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
OUTPUT_DIR  = Path("images_purified")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# enhance image
def _enhance(gray: np.ndarray) -> np.ndarray:
    den   = cv2.fastNlMeansDenoising(gray, h=15,
                                     templateWindowSize=7,
                                     searchWindowSize=21)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    eq    = clahe.apply(den)
    th    = cv2.adaptiveThreshold(eq, 255,
                                  cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 35, 10)
    kern  = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    return cv2.morphologyEx(th, cv2.MORPH_OPEN, kern)

def preprocess_image(path: Path) -> np.ndarray:
    logging.info(f"Cleaning {path.name}")
    img = cv2.imread(str(path))
    if img is None:                              # Pillow fallback
        img = np.array(Image.open(path).convert("RGB"))[..., ::-1]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return _enhance(gray)

# main
def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python purifier.py <input_path>")
        sys.exit(1)

    target = Path(sys.argv[1])

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = [p for p in target.iterdir() if p.suffix.lower() in VALID_EXT]
    else:
        print("❌ Input must be an existing file or directory")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for p in files:
        try:
            clean = preprocess_image(p)
            out_img = OUTPUT_DIR / p.name           # overwrite or add
            cv2.imwrite(str(out_img), clean)
            logging.info(f"✔ Saved → {out_img.name}")
        except Exception as e:
            logging.exception(f"Failed on {p.name}: {e}")
            sys.exit(1)

    logging.info("✅ Complete")

if __name__ == "__main__":
    main()
