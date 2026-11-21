# SarkariSathi AI

Multilingual (English / हिंदी / मराठी, plus romanised Marathi) retrieval-augmented assistant for Indian government schemes. Answers are grounded in indexed PDFs, cite their sources, and abstain when the documents do not contain the answer.

> **Read this first – data status.** The bundled corpus is **10 sample schemes × 3 languages (30 PDFs) written by the project author as fixtures — not official government documents**, and the Hindi/Marathi text and golden questions are **not yet verified by native speakers**. Everything is labelled `sample_fixture` in the API and UI. To use real data, drop official PDFs in `data/raw/pdfs/`, list them in `data/raw/manifest.json` (or use `scripts/add_scheme.py`) and re-run ingestion. Always verify scheme rules on official portals.

## Quick start (laptop, no GPU, no API key)

Requirements: Python 3.11+, Node 18+, optionally Tesseract.

```bash
# 1. backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cd .. && cp .env.example .env
python backend/scripts/ingest.py                       # (re)build chunks from data/raw/pdfs (already prebuilt in repo)
cd backend && uvicorn app.main:app --reload            # http://localhost:8000/docs

# 2. frontend (new terminal)
cd frontend && npm install && npm run dev              # http://localhost:5173 (proxies /api to :8000)
```

Without a key the app runs in **offline extractive mode**: answers are verbatim, cited sentences from the best passage. 

## Optional: LLM answers (Groq)
1. Create a free key at <https://console.groq.com/keys>.
2. Put it in `.env`: `GROQ_API_KEY=...` (never commit `.env`; it is git-ignored). `LLM_PROVIDER=auto` then uses Groq. Any OpenAI-compatible endpoint (OpenRouter, Ollama…) works with `LLM_PROVIDER=openai_compat`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.

## Optional: neural embeddings and reranker
```bash
pip install -r backend/requirements-ml.txt     # torch + sentence-transformers (several GB)
# .env: EMBED_MODEL=bge-m3  (or multilingual-e5 / labse)  USE_RERANKER=true
```
First start downloads the models from Hugging Face. If they cannot load, the API falls back to lexical retrieval and reports it in `/api/health`.

## Optional: OCR for scanned / legacy-font PDFs
Install Tesseract (`apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar`, or `brew install tesseract tesseract-lang`). If the `mar` model is missing, run `bash backend/scripts/setup_tessdata.sh` (needs internet) and set `TESSDATA_DIR`. Check: `python backend/scripts/ocr_check.py`.

## Docker
```bash
cp .env.example .env
docker compose up --build        # UI http://localhost:8080  API http://localhost:8000/docs
```
Single-container image (API + UI) for Render / HF Spaces: root `Dockerfile`, see `deploy/README.md`. **Docker builds and deployments were not tested in the build sandbox.**

## Evaluate
```bash
python backend/scripts/setup_data.py               # sample PDFs -> ingest -> golden set -> validation
python backend/scripts/run_eval.py --suite all     # writes data/evaluation/results/*.json and docs/RESULTS.md
cd backend && pytest -q                            # 50 tests
cd frontend && npm test                            # 6 tests
```
Golden set: 186 questions (18.8% unanswerable; en/hi/mr/romanised-mr). Human verification: edit `data/evaluation/golden_review.csv`, then `python backend/scripts/apply_review.py`. Measured results and caveats: [`docs/RESULTS.md`](docs/RESULTS.md). Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## API
`POST /api/chat` · `POST /api/chat/stream` (SSE: stage, sources, token, done) · `GET /api/schemes`, `/api/schemes/{id}` · `GET /api/suggestions?lang=` · `GET /api/health`.

## Demo queries
* `Who is eligible for PM-KISAN?` · `पीएम किसान योजना के लिए कौन पात्र है?` · `पीएम किसान साठी कोण पात्र आहे?` · `ujjwala yojanasathi kagdapatre konti lagtat?` · an out-of-scope one that abstains: `What is the capital of France?` (note: questions about a *known scheme* whose specific fact is missing, e.g. a helpline number, are often **not** refused in offline mode – see limitations)

## Known limitations
See `docs/RESULTS.md`. Highlights: sample corpus (10 schemes, not 30–50); unverified Hindi/Marathi; neural models, reranker and LLM were **not run** in the build sandbox (rows marked NOT RUN); oracle translation rows are upper bounds; extractive faithfulness is high by construction; ~69% abstention on unanswerable questions; romanised-Marathi support is weakest; Tesseract `mar` model absent in the sandbox.
