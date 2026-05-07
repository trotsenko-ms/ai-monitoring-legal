# validator-edo

**Версія:** 1.0
**Тип:** Validator
**Модель:** claude-haiku-4-5

## Призначення

Валідує результати monitor-edo. Для кожного знайденого документа виконує чотири механічні перевірки і формує email-дайджест для legal.monitor.ai@gmail.com.

## Місце в pipeline

```
monitor-edo ── validator-edo ── email [ЕДО]
```

## Вхід

Останній артефакт з `runs/monitor-edo/{timestamp}.json` за схемою `shared/schemas/monitor-artifact.schema.json`.

## Вихід

- `runs/validator-edo/{timestamp}.json` — validated artifact за схемою `shared/schemas/validated-artifact.schema.json`
- Email на `legal.monitor.ai@gmail.com` з темою `[ЕДО] Дайджест моніторингу за {від} — {до}`

## Перевірки per item

| Перевірка | Критерій |
|-----------|----------|
| `url_accessible` | URL повертає HTTP 200 |
| `document_found` | На сторінці ідентифіковано реквізити документа |
| `date_in_period` | Дата публікації потрапляє у розрахунковий period |
| `keywords_match` | Документ відповідає тематиці ЕДО/КЕП/архів |

## Статуси валідації

- **valid** — всі 4 перевірки пройдено, включається до дайджесту
- **invalid** — відхилено (false positive), НЕ включається до дайджесту
- **uncertain** — не вдалось однозначно перевірити, включається з позначкою

## Розклад

| Час (Київ) | UTC cron | Тригер |
|------------|----------|--------|
| 08:30 | `30 5 * * *` | cron (після monitor-edo) |
| За запитом | — | команда «ЕДО» |

## Credentials

Email надсилається через Gmail SMTP. Credentials зберігаються в GitHub Secrets:
- `GMAIL_SENDER` — адреса відправника
- `GMAIL_APP_PASSWORD` — App Password від Google акаунта

## Файли

| Файл | Опис |
|------|------|
| `prompt.md` | System prompt агента |
| `config.json` | Параметри запуску |
| `README.md` | Цей документ |
