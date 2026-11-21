# API only (use with frontend/Dockerfile via docker-compose). Build context = repo root.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt
# Optional neural models (large: torch + sentence-transformers). Build with --build-arg WITH_ML=1
ARG WITH_ML=0
COPY backend/requirements-ml.txt backend/requirements-ml.txt
RUN if [ "$WITH_ML" = "1" ]; then pip install -r backend/requirements-ml.txt; fi
COPY backend backend
COPY data data
EXPOSE 8000
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
