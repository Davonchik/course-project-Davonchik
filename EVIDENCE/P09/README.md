# P09 - SBOM & SCA Evidence

Этот каталог содержит артефакты автоматической генерации SBOM и сканирования уязвимостей зависимостей.

## Структура

- `sbom.json` — Software Bill of Materials в формате CycloneDX JSON
  - Генерируется инструментом Syft v0.102.0 (фиксированная версия для воспроизводимости)
  - Содержит все зависимости проекта (Python packages из `requirements*.txt`).
  - Включает метаданные о коммите, workflow run и времени генерации

- `sca_report.json` — Полный отчёт SCA (Software Composition Analysis)
  - Генерируется инструментом Grype v0.75.0 (фиксированная версия для воспроизводимости) на основе SBOM
  - Содержит детальную информацию о всех найденных уязвимостях (до применения waivers)
  - Формат: JSON с полями `matches`, `source`, `distro`

- `sca_report.filtered.json` — Отфильтрованный отчёт SCA
  - Содержит только уязвимости, которые не были waived
  - Используется для генерации сводки и анализа
  - Создаётся после применения waivers из `policy/waivers.yml`

- `sca_report.waived.json` — Список waived уязвимостей
  - Содержит уязвимости, которые были исключены через waivers
  - Показывает количество и детали waived findings
  - Используется для отслеживания исключений

- `sca_summary.md` — Краткая сводка по уязвимостям
  - Агрегированная статистика по severity (Critical/High/Medium/Low) из filtered-отчёта
  - Топ-10 Critical/High уязвимостей с описаниями
  - Количество waived findings
  - Ссылки на workflow run и коммит

## Применение waivers

Workflow автоматически применяет waivers из `policy/waivers.yml`:
- Сопоставляет CVE ID, package name и version
- Проверяет срок действия waiver (expires_at)
- Исключает waived уязвимости из filtered-отчёта
- Сохраняет список waived findings в отдельный файл

## Использование

### Для DS-раздела итогового отчёта

Эти артефакты используются для демонстрации:
- **DS1** — SBOM и уязвимости зависимостей (SCA) в контексте проекта
- Трассируемость зависимостей и их уязвимостей
- Процесс управления уязвимостями через waivers

### Связь с другими практиками

- **P08 (CI/CD)**: Workflow `ci-sbom-sca.yml` интегрирован в общий CI/CD процесс
- **SBOM для образа**: В `ci.yml` генерируется отдельный SBOM для Docker-образа (job `docker-build-and-scan`)
- **Политика waivers**: Исключения оформляются в `policy/waivers.yml` и автоматически применяются

## Workflow

Артефакты автоматически генерируются при:
- Изменении Python файлов или `requirements*.txt`
- Изменении `package.json` или `package-lock.json`
- Изменении самого workflow файла
- Ручном запуске через `workflow_dispatch`
- Создании/обновлении Pull Request

Workflow: `.github/workflows/ci-sbom-sca.yml`

### Jobs

- `sbom_sca` — генерирует SBOM, выполняет SCA, применяет waivers, создаёт сводку
- `commit-evidence` — коммитит артефакты обратно в ветку (только при `workflow_dispatch`)

## Воспроизводимость

- Версии инструментов фиксированы:
  - Syft: v0.102.0
  - Grype: v0.75.0
- Каждый прогон привязан к конкретному коммиту через `github.sha`
- Артефакты доступны в GitHub Actions на 90 дней
- При ручном запуске артефакты автоматически коммитятся обратно в ветку
