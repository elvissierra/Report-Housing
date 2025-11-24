FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Optional: system deps for scientific stack (pandas/numpy wheels usually avoid heavy build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY dev.requirements.txt .
RUN pip install --no-cache-dir -r dev.requirements.txt

# Copy backend code
COPY . .

EXPOSE 8000

# Dev-friendly: enable --reload for hot reload in container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]