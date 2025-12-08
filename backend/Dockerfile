# =============================
# Stage 1: Build the Vue frontend
# =============================
FROM node:20-alpine AS frontend-build

# Work at /frontend inside the build container
WORKDIR /frontend

# Install dependencies
# These paths are relative to the *build context root* (the repo root),
# so we reference the frontend folder explicitly.
COPY frontend/package*.json ./
RUN npm install

# Copy the rest of the frontend source and build it
COPY frontend/ ./
# Vite's default "production" mode reads .env.production
RUN npm run build

# =============================
# Stage 2: Backend + built frontend
# =============================
FROM python:3.12-slim AS backend

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# System deps for scientific Python (if needed by pandas, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
# Again, paths are relative to the build context root, so we point at backend/
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code into /app
COPY backend/ ./

# Copy built frontend into a path that matches main.py's DEFAULT_STATIC_DIR
# DEFAULT_STATIC_DIR resolves to /frontend/dist at runtime, so we put it there.
COPY --from=frontend-build /frontend/dist /frontend/dist

# Render sets $PORT; default to 8000 for local "docker run" usage
ENV PORT=8000

# Use sh -c so we can expand ${PORT}
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]