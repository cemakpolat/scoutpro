FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    netcat-openbsd \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./shared /app/shared
COPY analytics-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY analytics-service/ .

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8012/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012", "--workers", "4"]
