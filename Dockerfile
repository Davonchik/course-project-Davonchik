# # Build stage
# FROM python:3.11-slim AS build
# WORKDIR /app
# COPY requirements.txt requirements-dev.txt ./
# RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt
# COPY . .
# RUN pytest -q

# # Runtime stage
# FROM python:3.11-slim
# WORKDIR /app
# RUN useradd -m appuser
# COPY --from=build /usr/local/lib/python3.11 /usr/local/lib/python3.11
# COPY --from=build /usr/local/bin /usr/local/bin
# COPY . .
# EXPOSE 8000
# HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
# USER appuser
# ENV PYTHONUNBUFFERED=1
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM python:3.12-slim

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Установка системных зависимостей (если нужны, например, для psycopg2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем ТОЛЬКО зависимости — для кэширования
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Порт приложения
EXPOSE 8000

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
