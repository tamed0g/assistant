# ==========================================
# Этап 1: Сборка красивого React-сайта
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Копируем файлы для установки зависимостей
COPY frontend_src/package*.json ./
RUN npm install

# Копируем весь исходный код фронтенда и собираем его
COPY frontend_src/ .
RUN npm run build
# После этого появится готовая папка /app/frontend/dist (с assets)

# ==========================================
# Этап 2: Сборка Python бэкенда (FastAPI)
# ==========================================
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Python пакетов
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ваш бэкенд код
COPY app/ ./app/

# САМОЕ ГЛАВНОЕ: Копируем СОБРАННЫЙ сайт из первого этапа в папку static!
COPY --from=frontend-builder /app/frontend/dist ./static

ENV PORT=8000
EXPOSE 8000

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"