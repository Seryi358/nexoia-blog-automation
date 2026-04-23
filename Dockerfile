FROM python:3.12-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app/ ./app/
COPY seed_content_plan.py .
COPY content_plan.json* ./

# Data dir must be persisted via volume mount in production.
RUN mkdir -p /app/data
VOLUME ["/app/data"]

# PORT is overridable (EasyPanel routes the domain to this port). Default 80
# matches EasyPanel's default domain config; change via env if you front the
# container behind a custom proxy.
ENV PORT=80
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD python -c "import os, httpx; r = httpx.get(f'http://localhost:{os.environ.get(\"PORT\",\"80\")}/health', timeout=3); assert r.status_code == 200"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-80}"]
