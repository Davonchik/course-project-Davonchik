# Docker Setup для Reading List Frontend

## Быстрый старт

### 1. Сборка и запуск
```bash
# Использовать готовый скрипт
./docker-build.sh

# Или вручную
docker build -t reading-list-frontend .
docker run -d --name reading-list-frontend -p 3000:80 reading-list-frontend
```

### 2. Использование docker-compose
```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f
```

## Архитектура

### Multi-stage build
- **Stage 1 (builder)**: Node.js 18 Alpine для сборки React приложения
- **Stage 2 (production)**: Nginx Alpine для обслуживания статических файлов

### Оптимизации
- Минимальный размер образа (nginx:alpine)
- Gzip сжатие для статических ресурсов
- Кэширование статических файлов (1 год)
- Безопасные заголовки HTTP

## Конфигурация

### Переменные окружения
- `REACT_APP_API_URL` - URL бэкенда (по умолчанию: http://localhost:8000)

### Порты
- `80` - HTTP порт внутри контейнера
- `3000` - внешний порт (настраивается в docker-compose.yml)

### Health Check
- Endpoint: `/health`
- Проверка каждые 30 секунд
- Timeout: 10 секунд

## Команды управления

### Основные команды
```bash
# Сборка образа
docker build -t reading-list-frontend .

# Запуск контейнера
docker run -d --name reading-list-frontend -p 3000:80 reading-list-frontend

# Остановка контейнера
docker stop reading-list-frontend

# Удаление контейнера
docker rm reading-list-frontend

# Просмотр логов
docker logs reading-list-frontend

# Вход в контейнер
docker exec -it reading-list-frontend sh
```

### Docker Compose команды
```bash
# Запуск в фоне
docker-compose up -d

# Пересборка и запуск
docker-compose up --build -d

# Остановка
docker-compose down

# Просмотр статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f reading-list-frontend
```

## Развертывание в продакшене

### 1. Настройка переменных окружения
```bash
# Создать .env файл
echo "REACT_APP_API_URL=https://api.yourdomain.com" > .env
```

### 2. Сборка для продакшена
```bash
# Сборка с продакшен переменными
docker build --build-arg REACT_APP_API_URL=https://api.yourdomain.com -t reading-list-frontend:prod .
```

### 3. Запуск в продакшене
```bash
# С nginx reverse proxy
docker run -d \
  --name reading-list-frontend \
  -p 80:80 \
  -e REACT_APP_API_URL=https://api.yourdomain.com \
  reading-list-frontend:prod
```

## Мониторинг

### Health Check
```bash
# Проверка здоровья
curl http://localhost:3000/health

# Должен вернуть: "healthy"
```

### Логи
```bash
# Просмотр логов nginx
docker logs reading-list-frontend

# Просмотр логов в реальном времени
docker logs -f reading-list-frontend
```

## Troubleshooting

### Проблемы с CORS
Убедитесь, что бэкенд настроен для работы с фронтендом:
- Добавьте домен фронтенда в CORS настройки
- Проверьте переменную `REACT_APP_API_URL`

### Проблемы с роутингом
Nginx настроен для SPA - все маршруты перенаправляются на `index.html`

### Проблемы с кэшированием
Статические файлы кэшируются на 1 год. Для обновления:
```bash
docker-compose down
docker-compose up --build -d
```

## Размер образа
- **Исходный размер**: ~50MB (nginx:alpine)
- **С приложением**: ~60-80MB
- **Оптимизированный**: Gzip сжатие, минификация JS/CSS
