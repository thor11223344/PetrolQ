FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (build-essential for C extensions, libpq for postgres, tesseract for OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install CPU-only torch first to save space, then remaining requirements
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend and data
COPY backend/ ./backend/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Default port for Hugging Face Spaces is 7860
ENV PORT=7860
EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
