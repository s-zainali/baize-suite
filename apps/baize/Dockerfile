# Multi-stage build: compile the frontend, then serve it from the Python image.

# ---- stage 1: build the frontend ----
    ARG NODE_VERSION=24.19.0
    ARG PYTHON_VERSION=3.14.7
    
    FROM node:${NODE_VERSION} AS frontend
    WORKDIR /frontend
    
    # Declare the ARG before any COPY or npm commands so Render's injected build-arg is available
    ARG VITE_LICENSE_SERVER_URL
    ENV VITE_LICENSE_SERVER_URL=$VITE_LICENSE_SERVER_URL
    
    COPY frontend/package*.json ./
    RUN npm install
    COPY frontend/ ./
    RUN npm run build
    
    # ---- stage 2: python runtime ----
    FROM python:${PYTHON_VERSION} AS runtime
    
    ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        FLASK_APP=api/index.py \
        APP_ROLE=all \
        MIGRATE_ON_START=0 \
        PORT=5000
    
    WORKDIR /app/backend
    
    COPY backend/requirements.txt ./
    RUN pip install --no-cache-dir -r requirements.txt
    
    COPY backend/ ./
    COPY --from=frontend /backend/dist ./dist
    
    RUN chmod +x entrypoint.sh
    EXPOSE 5000
    ENTRYPOINT ["./entrypoint.sh"]