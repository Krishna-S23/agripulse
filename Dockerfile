# ---------- Stage 1: build the React frontend ----------
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/vite.config.js ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: Python backend + agents + bundled frontend ----------
FROM python:3.12-slim AS runtime
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ ./agents/
COPY backend/ ./backend/
COPY --from=frontend-build /frontend/dist ./backend/static

ENV AGRIPULSE_MOCK_DATA=0
ENV PORT=8080
WORKDIR /app/backend

EXPOSE 8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
