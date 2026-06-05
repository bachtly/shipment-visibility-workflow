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
RUN pip install --no-cache-dir \
    "dbos==2.23.0" \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.30" \
    "psycopg[binary]>=3.2" \
    "sqlalchemy>=2.0" \
    "pydantic>=2.0" \
    "python-dotenv>=1.0" \
    "sse-starlette>=2.0"
COPY backend/app ./app
COPY --from=frontend-builder /frontend/dist ./static
ENV PYTHONPATH=/app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
