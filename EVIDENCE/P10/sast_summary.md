# SAST & Secrets Summary

**Generated:** 2024-12-02  
**Workflow:** Security - SAST & Secrets  
**Commit:** `${{ github.sha }}` (заполняется при генерации в CI)

## Semgrep Findings

### Статистика по Severity

- **WARNING:** 1 finding
- **INFO:** 1 finding (ложное срабатывание)
- **ERROR:** 0 findings

### Детальный триаж

#### 1. `py-unsafe-password-default` (WARNING)
- **Файл:** `config.py:7`
- **Проблема:** Дефолтное значение пароля БД `"postgres"`
- **Статус:** ✅ **Принято как допустимое для dev-окружения**
- **Обоснование:** 
  - Это dev-значение по умолчанию для локальной разработки
  - В продакшене переопределяется через переменные окружения (`.env` файл или secrets manager)
  - Используется `pydantic_settings.BaseSettings`, который загружает значения из `env_file=".env"`
  - В CI/CD используются секреты из GitHub Secrets
- **Действие:** Оставляем как есть, т.к. это стандартная практика для dev-окружения

#### 2. `py-jwt-decode-no-verification` (INFO)
- **Файл:** `adapters/security.py:62-68`
- **Проблема:** Semgrep предупреждает о возможном отсутствии проверки подписи JWT
- **Статус:** ❌ **Ложное срабатывание**
- **Обоснование:**
  - `jwt.decode()` из библиотеки `PyJWT` **по умолчанию проверяет подпись** (`verify_signature=True`)
  - Мы явно указываем `algorithms=[settings.JWT_ALGORITHM]` и `issuer=settings.JWT_ISSUER`
  - Код корректно реализует проверку подписи и claims
- **Действие:** Игнорируем, т.к. это false positive. Правило можно уточнить или отключить для этого случая

### Исправленные проблемы

- ✅ Исправлена ошибка парсинга правила `py-broad-exception-handling` в `security/semgrep/rules.yml`

## Gitleaks Findings

**Статус:** Отчёт будет сгенерирован при следующем запуске workflow.

**Конфигурация allowlist:**
- Исключены dev-секреты в `config.py` (JWT_SECRET, POSTGRES_PASSWORD)
- Исключены директории: `EVIDENCE/`, `__pycache__/`, `node_modules/`, `.git/`, `build/`

## Итоговые действия

1. ✅ **Semgrep:** Найдено 2 findings, оба обработаны (1 принят как допустимый для dev, 1 - false positive)
2. ⏳ **Gitleaks:** Ожидается генерация отчёта при следующем запуске workflow
3. ✅ **Правила Semgrep:** Исправлена ошибка парсинга, правила работают корректно
4. ✅ **Конфигурация:** Allowlist в `.gitleaks.toml` настроен для исключения известных false positives

## Рекомендации

1. **Для продакшена:** Убедиться, что все секреты загружаются из переменных окружения/secrets manager
2. **Мониторинг:** Регулярно запускать SAST & Secrets scanning в CI/CD
3. **Триаж:** Периодически пересматривать findings и обновлять allowlist при необходимости

## Ссылки

- Workflow: `.github/workflows/ci-sast-secrets.yml`
- Semgrep правила: `security/semgrep/rules.yml`
- Gitleaks конфигурация: `security/.gitleaks.toml`
- Полные отчёты: `EVIDENCE/P10/semgrep.sarif`, `EVIDENCE/P10/gitleaks.json`

