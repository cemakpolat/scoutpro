FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/ is mounted as a volume at runtime; DATA_ROOT tells the app where it is
ENV DATA_ROOT=/app/data
ENV PORT=7000

EXPOSE 7000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7000"]
