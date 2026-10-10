# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend:/app \
    PORT=5000 \
    FLASK_ENV=production

# Install system dependencies including Tesseract OCR engine and English traineddata
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies first for optimal Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files and runtime assets
COPY backend/ ./backend/
COPY wsgi.py ./
COPY README.md ./

# Ensure uploads directory exists
RUN mkdir -p backend/static/uploads

# Expose default port (Render dynamically sets PORT env variable at runtime)
EXPOSE 5000

# Start Gunicorn WSGI server:
# - workers=1, threads=4: conservative memory footprint (<250MB) optimal for Render Free Tier (512MB limit)
# - timeout=120: prevents worker timeouts during OCR processing and cold starts
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 4 --timeout 120 wsgi:app"]
