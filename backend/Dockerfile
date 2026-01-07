FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

# Metadata
LABEL maintainer="hthhistorybot"
LABEL description="Lịch Sử 12 AI Tutor API - FastAPI Backend"

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    fontconfig \
    libfontconfig1 \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

RUN mkdir -p /home/appuser/.local
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

WORKDIR /app

COPY --chown=appuser:appuser app/ ./app/

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

USER appuser

EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
