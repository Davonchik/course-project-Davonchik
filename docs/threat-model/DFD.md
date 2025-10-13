# DFD — Data Flow Diagram

## Диаграмма (Mermaid)

```mermaid
flowchart LR
  %% --- Client boundary ---
  subgraph Client ["Trust Boundary: Client"]
    U["User / Frontend (SPA)"]
  end

  %% --- Edge boundary ---
  subgraph Edge ["Trust Boundary: Edge / Public"]
    API["Reading List API (FastAPI + AuthMiddleware)"]
  end

  %% --- Core boundary ---
  subgraph Core ["Trust Boundary: Core / Platform"]
    SECRETS[".env / CI Secrets: JWT_SECRET, JWT_ISSUER"]
  end

  %% --- Data boundary ---
  subgraph Data ["Trust Boundary: Data"]
    DB["PostgreSQL: users, entries, refresh_tokens, revoked_tokens"]
  end

  %% --- Flows Client -> API ---
  U -->|"F1: POST /auth/register"| API
  U -->|"F2: POST /auth/login"| API
  U -->|"F5: /entries* (Bearer)"| API
  U -->|"F7: POST /auth/refresh"| API
  U -->|"F8: POST /auth/logout"| API
  U -->|"F10: GET /admin"| API

  %% --- Flows API -> DB ---
  API -->|"F3: create user/entry"| DB
  API -->|"F4: persist refresh"| DB
  API -->|"F6: update entries"| DB
  API -->|"F7b: rotate refresh"| DB
  API -->|"F8b: revoke/blacklist jti"| DB
  API -->|"F10b: list users"| DB

  %% --- Load secrets ---
  API -.->|"F9: load secrets"| SECRETS
```

## Таблица потоков

| ID   | Откуда → Куда       | Канал / Протокол     | Данные / PII                    | Комментарий                                          |
|------|----------------------|----------------------|----------------------------------|------------------------------------------------------|
| F1   | Client → API         | HTTPS, JSON          | email, password                  | Регистрация пользователя                             |
| F2   | Client → API         | HTTPS, form-urlencoded | email, password               | Аутентификация по паролю                             |
| F3   | API → DB             | SQL                  | email, hashed_password, device_id | Создание записи пользователя в базе                 |
| F4   | API → DB             | SQL                  | refresh_token, jti, device_id   | Сохранение refresh-токена и его метаданных          |
| F5   | Client → API         | HTTPS, Bearer token  | JWT (access)                    | Работа с записями: создание, получение, изменение    |
| F6   | API → DB             | SQL                  | title, kind, link, status       | CRUD-операции с записями чтения                     |
| F7   | Client → API         | HTTPS, JSON          | refresh_token, device_id        | Запрос обновления access-токена                      |
| F7b  | API → DB             | SQL                  | old_refresh, new_refresh, jti   | Ротация refresh-токена: вставка нового, revoke старого |
| F8   | Client → API         | HTTPS, JSON + Bearer | refresh_token, jti, device_id   | Logout: отзыв refresh-токена                        |
| F8b  | API → DB             | SQL                  | jti, device_id                  | Занесение в blacklist и удаление refresh по устройству |
| F9   | API → SECRETS        | dotenv / env / CI    | JWT_SECRET, JWT_ISSUER          | Загрузка секретов при старте приложения             |
| F10  | Client → API         | HTTPS, Bearer token  | JWT (access)                    | Доступ к административному API                      |
| F10b | API → DB             | SQL                  | user_id, email (all users)      | Получение списка всех пользователей (админка)       |нет
