#!/usr/bin/env bash
# Download Tesseract language data (English, Hindi, Marathi) into data/tessdata.
# Needs internet access to github.com. Also install the tesseract binary itself:
#   Ubuntu/Debian: sudo apt install tesseract-ocr     macOS: brew install tesseract     Windows: UB-Mannheim installer
set -euo pipefail
DEST="$(cd "$(dirname "$0")/../.." && pwd)/data/tessdata"
mkdir -p "$DEST"
for lang in eng hin mar; do
  echo "downloading $lang ..."
  curl -fsSL -o "$DEST/$lang.traineddata" "https://github.com/tesseract-ocr/tessdata_fast/raw/main/$lang.traineddata"
done
echo "done -> $DEST (the app uses it automatically via TESSDATA_DIR / data/tessdata)"
