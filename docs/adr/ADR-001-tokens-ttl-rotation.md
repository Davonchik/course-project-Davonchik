# ADR-001: Токены — TTL, ротация refresh, blacklist
Дата: 2025-10-15
Статус: Accepted

## Context
В сервисе используются JWT access/refresh токены. Требуется: ограниченный срок жизни (TTL), привязка к устройству, одноразовость refresh (ротация), и отзыв/blacklist для access/refresh. Это снижает риски R2 (replay refresh), R11 (неполный logout), а также упрощает принудительный logout.

## Decision
- Access-токен: TTL 5 минут (`settings.ACCESS_TOKEN_EXPIRE_MINUTES`).
- Refresh-токен: TTL 30 минут (`settings.REFRESH_TOKEN_EXPIRE_MINUTES`).
- Оба токена содержат обязательные поля: `sub`, `iss`, `iat`, `exp`, `type`, `jti`; также `device` для привязки к устройству.
- При refresh выполняется ротация: текущий refresh помечается `revoked=True` в `RefreshToken`, создаётся новый refresh и записывается как активный (`services.tokens.revoke_refresh_by_jti`, `create_refresh_record`).
- При logout:
  - Текущий access добавляется в `RevokedToken` (blacklist), если device совпадает.
  - Все refresh для устройства `device_id` помечаются revoked (`revoke_refresh_for_device`).
  - Если передан refresh-токен в payload, он тоже добавляется в blacklist (`RevokedToken`).
- Middleware проверяет, что:
  - Токен типа `access`;
  - Его `jti` не в blacklist (`services.tokens.is_jti_blacklisted`).

## Consequences
- Плюсы: снижение риска re-use refresh; быстрый инцидент-отзыв через blacklist; минимизация ущерба компрометации access (короткий TTL).
- Минусы: дополнительные записи в БД (таблицы `RefreshToken`, `RevokedToken`), усложнение логики при logout/refresh.
- Влияние на DX/производительность: несущественное для типичных нагрузок; нужно следить за чисткой старых записей.

## Alternatives
- Keep-alive refresh без ротации: проще, но уязвим к replay атаке на refresh (не закрывает R2).
- Длинный TTL access (напр. 60 мин): меньше обращений к refresh, но увеличивает окно компрометации.
- Серверные сессии (stateful): надёжно с invalidation, но требует хранить сессии и sticky/общий сторедж.

## Security impact
- Снижение вероятности и воздействия R2/R11. Ключевые KPI: доля отклонённых повторно используемых refresh, среднее время до отзыва (TTI), отсутствие чужих `jti` в запросах.
- Связь с P03/P04: NFR-03/04/06; STRIDE R2/R11.

## Rollout plan / DoD
- DoD: тесты `tests/test_refresh.py`, `tests/test_logout.py`, `tests/test_login.py` зелёные; TTL берутся из `settings`.
- Rollout: фича уже включена. Для продакшна — добавить фоновую чистку устаревших записей и мониторинг попыток reuse (по `RevokedToken`).

## Links
- NFR-03 (TTL токенов), NFR-04 (ротация refresh), NFR-06 (унификация ошибок аутентификации), NFR-07 (секреты из env/CI)
- DFD Flows: F2 (login), F4 (persist refresh), F5 (protected endpoints, Bearer), F7 (refresh), F7b (rotate refresh), F8 (logout), F8b (blacklist)
- STRIDE/RISKS: R2, R11
- Код: `adapters/security.py`, `services/tokens.py`, `app/middleware.py`, `app/routers/auth.py`
- Тесты: `tests/test_refresh.py`, `tests/test_logout.py`, `tests/test_login.py`, `tests/test_tokens.py`, `tests/test_auth.py`
