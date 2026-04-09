FROM python:3.12-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app/ ./app/
COPY seed_content_plan.py .
COPY content_plan.json* ./

# Create data directory
RUN mkdir -p data

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8001/health'); assert r.status_code == 200"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
