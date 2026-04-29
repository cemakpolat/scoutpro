FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    netcat-openbsd \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY ./shared /app/shared
COPY video-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY video-service/ .

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8011/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011", "--workers", "4"]
