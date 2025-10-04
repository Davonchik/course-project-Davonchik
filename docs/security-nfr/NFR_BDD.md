# NFR_BDD.md — Приёмка в формате Gherkin

```
Feature: Ограниченный срок жизни токенов
  Scenario: Access токен недействителен через 5 минут
    Given пользователь получил access токен при логине
    When проходит более 5 минут
    Then запрос с этим токеном возвращает 401 Unauthorized
```

```
Feature: Ротация refresh токенов
  Scenario: Старый refresh не работает после обновления
    Given пользователь получил refresh токен
    When он обновляет его через POST /api/v1/auth/refresh
    Then старый refresh становится revoked и не может быть использован повторно
```

```
Feature: Авторизация по ролям
  Scenario: Пользователь видит только свои записи
    Given создана запись пользователем A и запись пользователем B
    When пользователь A делает GET /api/v1/entries
    Then он видит только свои записи
```

```
Feature: Ошибки аутентификации
  Scenario: Ошибочный пароль возвращает 401
    Given пользователь зарегистрирован с email и паролем
    When он делает POST /login с неверным паролем
    Then API возвращает 401 Unauthorized
```

# Негативные сценарии

```
Feature: Неверный формат токена
  Scenario: Пустой bearer токен отклоняется
    Given в запросе нет Authorization: Bearer <token>
    When пользователь обращается к /api/v1/entries
    Then API возвращает 401 Unauthorized с detail="Missing Authorization header"
```

```
Feature: Попытка доступа к чужой записи
  Scenario: Пользователь не может читать чужие записи
    Given пользователь A создал запись
    When пользователь B делает GET /api/v1/entries/{entry_id} этой записи
    Then API возвращает 404 Entry not found
```
