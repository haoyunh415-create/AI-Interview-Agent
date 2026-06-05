# syntax=docker/dockerfile:1
# ── AI Interview Copilot — FastAPI Backend ──
# Multi-stage: pip deps cached in a separate layer

# ── Stage 1: Dependencies ──
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──
FROM python:3.11-slim

WORKDIR /app

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy only the application code needed at runtime
# (Use .dockerignore to exclude tests, frontend, etc.)
COPY backend/ backend/
COPY agents/ agents/
COPY core/ core/
COPY db/ db/
COPY report/ report/
COPY pyproject.toml .
COPY .env.example .

# Create directories for persistent data
RUN mkdir -p data outputs/reports

ENV PYTHONUNBUFFERED=1

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8765/api/health || exit 1

VOLUME ["/app/data", "/app/outputs/reports"]

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8765"]
