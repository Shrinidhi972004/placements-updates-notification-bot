# -staGe 1: builder 
FROM python:3.11-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# stage 2: Runtime 
FROM python:3.11-slim
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY email_to_telegram_debug.py .

CMD ["python", "email_to_telegram_debug.py"]

