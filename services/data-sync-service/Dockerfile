FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy shared libraries
COPY services/shared /app/shared

# Copy entrypoint
COPY services/data-sync-service/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Install Python dependencies
COPY services/data-sync-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/data-sync-service/ /app/

# Default command runs the FastAPI REST API (scheduler is started in lifespan)
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012"]
