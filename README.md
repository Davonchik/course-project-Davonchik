# Reading List Service

Сервис для хранения и управления списоком книг/статей «к прочтению»  (HSE SecDev 2025).

### Цели
- Организовать хранение пользователей и их книг.
- Реализовать CRUD-операции над книгами и тегами.
- Обеспечить JWT-аутентификацию и авторизацию.
- Покрыть проект автотестами.

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
uvicorn app.main:app --reload
```

## Ритуал перед PR
```bash
ruff check --fix .
black .
isort .
pytest -q
pre-commit run --all-files
```

## Тесты
```bash
pytest -q
```

## CI
В репозитории настроен workflow **CI** (GitHub Actions) — required check для `main`.
Badge добавится автоматически после загрузки шаблона в GitHub.

## Контейнеры
```bash
docker build -t secdev-app .
docker run --rm -p 8000:8000 secdev-app
# или
docker compose up --build
```

## Эндпойнты
- `GET /health` → `{"status": "ok"}`
- `POST /items?name=...` — демо-сущность
- `GET /items/{id}`

## Формат ошибок
Все ошибки — JSON-обёртка:
```json
{
  "error": {"code": "not_found", "message": "item not found"}
}
```

## Security-требования

| Категория             | Требование                                                                                                    | Реализация в проекте |
|------------------------|---------------------------------------------------------------------------------------------------------------|-----------------------|
| **Аутентификация**    | Пароль пользователя должен быть длиной ≥ 6 символов.   | Валидация через `pydantic.Field(min_length=6)` в `RegisterIn`. |
| **Сессии**            | Access-токен живёт ≤ **5 минут**; Refresh-токен ≤ **30 минут**. Logout отзыв токенов по `device_id`. | Настройки `ACCESS_TOKEN_EXPIRE_MINUTES=5`, `REFRESH_TOKEN_EXPIRE_MINUTES=30`. Поддерживается logout с отзывом access/refresh токенов. |
| **Ошибки/ответы**     | Ошибки аутентификации унифицированы: `401 Unauthorized`, `403 Forbidden`. Причины не раскрываются детально.   | Все ошибки через `HTTPException` с кодами 401/403, тексты унифицированы. |
| **Секреты**           | JWT-секрет хранится в `settings.JWT_SECRET`.                                                            | Секреты загружаются из `.env`. |
| **Логи/аудит**        | Логируются запросы (uvicorn / FastAPI).                     | Базовое логирование HTTP-запросов. |
| **Приватность/ретеншн** | В БД храним минимально необходимую информацию: email, пароль (bcrypt), роль, активность. | В моделях `User` и `Entry` хранятся только необходимые поля. |

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
