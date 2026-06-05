# Stage 1 — build React SPA
FROM node:22-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2 — Python backend + built SPA
FROM python:3.12-slim AS final
WORKDIR /app
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY backend/app ./app
COPY --from=frontend-builder /frontend/dist ./static
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
