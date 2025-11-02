# ADR-004: RFC 7807 — Унификация ошибок и correlation tracking
Дата: 2025-11-02
Статус: Accepted

## Context
Текущая обработка ошибок возвращает различные форматы (`{"detail": ...}`) и может раскрывать чувствительные детали (stack traces, внутренние пути, причины отказа). Отсутствует correlation_id для трассировки запросов. Это приводит к риску R5 (утечка деталей ошибок) и усложняет отладку распределённых запросов.

## Decision
- Все HTTP-ошибки (401/403/422/500) возвращаются в формате RFC 7807 (`application/problem+json`):
  - Обязательные поля: `type`, `title`, `status`, `detail`, `correlation_id`.
  - Для 401/403: детали маскируются («Unauthorized», без причины).
  - Для 500: детали полностью скрыты («Internal server error»).
  - Для 422: добавляется массив `errors[]` с деталями валидации.
- Correlation ID:
  - Генерируется в `CorrelationIdMiddleware` (UUID) для каждого запроса.
  - Пишется в `request.state.correlation_id`.
  - Возвращается в заголовке `X-Correlation-ID` и в теле ответа.
- Безопасное логирование:
  - Удалены все `print()`.
  - `RequestLoggingMiddleware` пишет: method, path, status, correlation_id, user_id.
  - Логи ошибок (`app/errors.py`) содержат только correlation_id и уровень, без PII.
- Порядок мидлваров (outermost → innermost):
  - `CorrelationIdMiddleware` (первым устанавливает correlation_id)
  - `RequestLoggingMiddleware`
  - `AuthMiddleware`

## Alternatives
- Продолжать возвращать `{"detail": ...}`: проще, но риск утечек и нет трассировки.
- Логировать все детали (включая PII): удобно для дебага, но нарушает приватность и compliance.
- Использовать внешний трейсинг (OpenTelemetry): мощно, но избыточно для учебного проекта.

## Security impact
- Снижение вероятности R5. Индикаторы: отсутствие стэктрейсов/путей в 4xx/5xx; единый формат; correlation_id в каждом ответе.
- Связь с P03/P04: NFR-06 (ошибки аутентификации), R5 (утечка деталей), F2 (login flow).

## Rollout plan / DoD
- DoD:
  - Все 4xx/5xx возвращают problem+json с correlation_id.
  - Тесты: `tests/test_rfc7807.py` (401/422/500 + SQLi abuse).
  - Логи без PII; CI зелёный (ruff/black/isort/mypy/bandit + coverage ≥80%).
- Rollout: фича включена; при добавлении новых ручек/ошибок — использовать `problem(...)` или глобальные handlers.

## Consequences
- Плюсы: унификация формата ошибок, трассировка запросов, защита от утечек PII, соответствие NFR-06/R5.
- Минусы: чуть сложнее отладка локально (нужно смотреть correlation_id в логах); дополнительные мидлвары.
- DX: проще отлаживать продакшн-баги по correlation_id; единый контракт для фронтенда.

## Links
- NFR-06 (Унификация ошибок аутентификации)
- STRIDE/RISKS: R5 (утечка деталей ошибок)
- DFD Flows: F2 (login), F5 (entries), F10 (admin)
- Код: `app/errors.py`, `app/middleware.py`, `app/main.py`
- Тесты: `tests/test_rfc7807.py` (401/422/500 + SQL injection abuse)
