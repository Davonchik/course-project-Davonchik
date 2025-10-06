# Быстрый старт

## 1. Установка зависимостей
```bash
npm install
```

## 2. Настройка окружения
Создайте файл `.env` в корне проекта:
```env
REACT_APP_API_URL=http://localhost:8000
```

## 3. Запуск приложения
```bash
npm start
```

Приложение будет доступно по адресу: http://localhost:3000

## 4. Сборка для продакшна
```bash
npm run build
```

## Основные функции

### Аутентификация
- Регистрация: `/register`
- Вход: `/login`
- Автоматическое обновление токенов

### Управление записями
- Просмотр списка записей
- Фильтрация по статусу
- Пагинация
- Создание/редактирование/удаление записей

### Роли пользователей
- **User**: видит только свои записи
- **Admin**: видит все записи, может фильтровать по владельцу

## API требования

Убедитесь, что FastAPI бэкенд запущен на `http://localhost:8000` и поддерживает следующие эндпоинты:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `GET /api/v1/entries`
- `POST /api/v1/entries`
- `GET /api/v1/entries/{id}`
- `PATCH /api/v1/entries/{id}`
- `DELETE /api/v1/entries/{id}`

## Структура проекта

```
src/
├── api/           # API клиент
├── components/    # React компоненты
├── contexts/      # React контексты
├── types/         # TypeScript типы
└── App.tsx       # Главный компонент
```
