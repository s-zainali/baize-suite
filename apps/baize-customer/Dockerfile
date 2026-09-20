# Stage 1: Build the Vue Frontend within the Monorepo
FROM node:20-alpine AS frontend-builder
WORKDIR /app

# 1. Copy the root package files to initialize the workspace configuration
COPY package*.json ./
# Note: If you are using pnpm-workspace.yaml or yarn.lock, copy that here instead

# 2. Copy the package definitions for the UI package and your specific app
COPY packages/baize-ui/package*.json ./packages/baize-ui/
COPY apps/baize-customer/package*.json ./apps/baize-customer/

# 3. Install dependencies for the monorepo workspaces
RUN npm ci

# 4. Copy the actual source files needed for the compilation
COPY packages/baize-ui/ ./packages/baize-ui/
COPY apps/baize-customer/ ./apps/baize-customer/

# 5. Build your specific frontend application
RUN npm run build --workspace=apps/baize-customer/frontend

# Stage 2: Setup Python Backend & Bundle Static Files
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY apps/baize-customer/backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY apps/baize-customer/backend/ ./backend/

# FIX: Copy the compilation output from the correct baize-customer directory
COPY --from=frontend-builder /app/apps/baize-customer/dist /app/dist

WORKDIR /app/backend

# Expose port and run application via uvicorn
ENV PORT=10000
EXPOSE 10000

CMD uvicorn app:app --host 0.0.0.0 --port $PORT
