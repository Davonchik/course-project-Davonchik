# Reading List Service

Сервис для хранения и управления списоком книг/статей «к прочтению»  (HSE SecDev 2025).

### Цели
- Организовать хранение пользователей и их книг.
- Реализовать CRUD-операции над книгами и тегами.
- Обеспечить JWT-аутентификацию и авторизацию.
- Покрыть проект автотестами.

---

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

команда
```bash
docker compose up -d --build
```
подымет БД, [Бэкенд](http://localhost:8000/docs) и [Фронт](http://localhost:3000/login)

чтобы накатить миграцию, нужно сначала поднять контейнеры с помощью команды выше, а дальше ввести команду: `docker compose exec app alembic upgrade head`

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
docker compose up --build
```

## Эндпойнты
### Auth
- **POST /api/v1/auth/register**
  Регистрация пользователя.
  **Тело:** `{"email": "...", "password": "...", "device_id": "..."}`
  **Ответ:** TokenOut (access, refresh, device_id)

- **POST /api/v1/auth/login**
  Логин по email+паролю (OAuth2 form).
  **Заголовки:** `User-Agent`, `X-Device-Id` (optional)
  **Ответ:** TokenOut

- **POST /api/v1/auth/refresh**
  Обновление токенов по refresh.
  **Тело:** `{"refresh_token": "..."}`
  **Ответ:** TokenOut

- **GET /api/v1/auth/me**
  Данные о текущем пользователе.
  Требует access токен.
  **Ответ:** `{ "id": ..., "role": ... }`

- **POST /api/v1/auth/logout**
  Логаут: отзывает refresh по девайсу, кладёт access в блэклист.
  **Тело:** `{"device_id": "...", "refresh_token": "..."}`
  **Ответ:** `204 No Content`

### Entries
- **POST /api/v1/entries**
  Создать запись (книга/статья).
  **Тело:** `EntryCreate`
  **Ответ:** созданный объект

- **GET /api/v1/entries**
  Список записей.
  **Параметры:** `entry_status`, `limit`, `offset`, `owner_id` (только админ)
  **Ответ:** `{ items: [...], limit, offset, count }`

- **GET /api/v1/entries/{entry_id}**
  Получить запись по id (админ — любую, пользователь — только свою).
  **Ответ:** `Entry`

- **PATCH /api/v1/entries/{entry_id}**
  Обновить запись.
  **Тело:** `EntryUpdate`
  **Ответ:** обновлённый объект

- **DELETE /api/v1/entries/{entry_id}**
  Удалить запись.
  **Ответ:** `204 No Content`

### Admin
- **GET /api/v1/admin**
  Список пользователей (только админ).
  **Параметры:** `limit`, `offset`, `q` (поиск по email)
  **Ответ:** `[ { id, email }, ... ]`

## Формат ошибок
Все ошибки — JSON-обёртка:
```json
{
  "error": {"code": "not_found", "message": "item not found"}
}
```

---

## Security-требования

| Категория              | Шаблон формулировки                                                                                           | Конкретизация для Reading List |
|-------------------------|--------------------------------------------------------------------------------------------------------------|--------------------------------|
| **Аутентификация**     | Пароль пользователя должен быть длиной ≥ `<L>` символов.                                                      | Минимум 6 символов, проверка через `pydantic.Field(min_length=6)` в `RegisterIn`. |
| **Сессии**             | Срок жизни access-токена ≤ `<T_access>`; срок жизни refresh-токена ≤ `<T_refresh>`; logout отзывает все refresh по `<device_id>`. | Access = 5 минут, Refresh = 30 минут (см. `settings`). Logout отзывает токены по device_id. |
| **Ошибки/ответы**      | Ошибки аутентификации унифицированы: коды `401/403`, причины детально не раскрываются.                        | Все ошибки поднимаются через `HTTPException` с унифицированными текстами (`Invalid credentials`, `User not found`, `Forbidden`). |
| **Секреты**            | JWT-секрет хранится в `<secrets_manager>`; ротация ≤ `<D>` дней; доступ к секретам журналируется.              | JWT-секрет хранится в `.env` (`settings.JWT_SECRET`). Пока без автоматической ротации, можно добавить в CI/CD. |
| **Логи/аудит**         | ≥ `<P>%` критичных действий (login, register, refresh, logout) фиксируются; событие audit содержит actor, action, resource. | Базовое логирование HTTP-запросов через Uvicorn/FastAPI. Ошибки и операции аутентификации фиксируются. |
| **Приватность/ретеншн**| Храним только минимально необходимые данные `<минимально-необходимые>`.         | В `User` — только email, пароль (bcrypt), роль, активность. |
| **Авторизация**        | Доступ к ресурсам ограничен по ролям: пользователь видит только свои записи, админ имеет глобальный доступ.   | Проверка роли через `request.state.user['claims']['role']`. В `/entries` юзер видит только свои записи, админ — любые. |
| **Refresh-ротация**    | Refresh-токен используется только один раз; при обновлении старый немедленно помечается revoked.              | Реализовано в `refresh_token`: сначала `revoke_refresh_by_jti`, потом выдаётся новый refresh. |
| **Transport Security** | Все запросы и ответы передаются по HTTPS/TLS версии ≥ `<V>`; использование небезопасных протоколов блокируется. | В деплойменте используется HTTPS (TLS ≥ 1.2) — обязательное требование при публикации API. |

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
