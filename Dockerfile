# ==========================================
# Этап 1: Сборка красивого React-сайта
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Указываем правильный путь от корня проекта
COPY backend/frontend/frontend_src/package*.json ./
RUN npm ci

# Исходники (node_modules с хоста в .dockerignore — иначе ломаются бинарники в Linux)
COPY backend/frontend/frontend_src/ .
RUN npm run build

# ==========================================
# Этап 2: Сборка Python бэкенда (FastAPI)
# ==========================================
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Копируем requirements.txt из папки backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бэкенда из папки backend
COPY backend/app/ ./app/

# Копируем собранный сайт из первого этапа (тут путь менять не нужно, он внутри Docker)
COPY --from=frontend-builder /app/frontend/dist ./static

ENV PORT=8000
EXPOSE 8000

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"