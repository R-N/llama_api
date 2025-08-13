# === Build stage ===
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    dos2unix rsync git build-essential cmake && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual env
COPY . ./
RUN rm -rf .git
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

RUN sed -i 's/\r$//' /app/setup.sh /app/entrypoint.sh
RUN dos2unix /app/setup.sh /app/entrypoint.sh
RUN chmod +x /app/setup.sh /app/entrypoint.sh

RUN sh setup.sh

# === Final stage ===
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    dos2unix rsync libstdc++6 libffi-dev libgcc-s1 libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# Copy from builder
COPY --from=builder /app /app
COPY --from=builder /venv /venv

RUN sed -i 's/\r$//' /app/setup.sh /app/entrypoint.sh
RUN dos2unix /app/setup.sh /app/entrypoint.sh
RUN chmod +x /app/setup.sh /app/entrypoint.sh

# Set environment so Python uses our clean venv
ENV PATH="/venv/bin:$PATH"

RUN [ -f entrypoint.sh ] || (echo "ERROR: entrypoint.sh missing!" && exit 1)
RUN [ -f /app/entrypoint.sh ] || (echo "ERROR: /app/entrypoint.sh missing!" && exit 1)

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
