# -------- Stage 1: Builder --------
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Create a virtual environment and install deps
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# -------- Stage 2: Runtime --------
FROM python:3.11-slim

WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Ensure venv is used by default
ENV PATH="/opt/venv/bin:$PATH"

# Copy only the bot script (not your local venv/cache)
COPY email_to_telegram_debug.py .

# Run the bot
CMD ["python", "email_to_telegram_debug.py"]
