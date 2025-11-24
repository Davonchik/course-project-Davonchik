# P09 - SBOM & SCA Evidence

Этот каталог содержит артефакты автоматической генерации SBOM и сканирования уязвимостей зависимостей.

## Структура

- `sbom.json` — Software Bill of Materials в формате CycloneDX JSON
  - Генерируется инструментом Syft
  - Содержит все зависимости проекта (Python packages из `requirements*.txt`)
  - Включает метаданные о коммите, workflow run и времени генерации

- `sca_report.json` — Полный отчёт SCA (Software Composition Analysis)
  - Генерируется инструментом Grype на основе SBOM
  - Содержит детальную информацию о найденных уязвимостях
  - Формат: JSON с полями `matches`, `source`, `distro`

- `sca_summary.md` — Краткая сводка по уязвимостям
  - Агрегированная статистика по severity (Critical/High/Medium/Low)
  - Топ-10 Critical/High уязвимостей с описаниями
  - Ссылки на workflow run и коммит

## Использование

### Для DS-раздела итогового отчёта

Эти артефакты используются для демонстрации:
- **DS1** — SBOM и уязвимости зависимостей (SCA) в контексте проекта
- Трассируемость зависимостей и их уязвимостей
- Процесс управления уязвимостями

### Связь с другими практиками

- **P08 (CI/CD)**: Workflow `ci-sbom-sca.yml` интегрирован в общий CI/CD процесс
- **SBOM для образа**: В `ci.yml` генерируется отдельный SBOM для Docker-образа (job `docker-build-and-scan`)
- **Политика waivers**: Исключения оформляются в `policy/waivers.yml`

## Workflow

Артефакты автоматически генерируются при:
- Изменении Python файлов или `requirements*.txt`
- Изменении `package.json` или `package-lock.json`
- Ручном запуске через `workflow_dispatch`

Workflow: `.github/workflows/ci-sbom-sca.yml`

## Воспроизводимость

- Версии инструментов фиксированы (Syft/Grype:latest)
- Каждый прогон привязан к конкретному коммиту через `github.sha`
- Артефакты доступны в GitHub Actions на 90 дней
