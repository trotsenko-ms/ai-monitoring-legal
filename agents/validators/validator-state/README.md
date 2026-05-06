# validator-state

**Версія:** 1.0
**Тип:** Validator
**Модель:** claude-haiku-4-5

## Призначення

Валідує консолідовані результати гілки держорганів. Для кожного документа з трьох джерел (ВРУ, КМУ, НБУ) виконує чотири механічні перевірки і формує email-дайджест для legal.monitor.ai@gmail.com.

## Місце в pipeline

```
monitor-rada-bills ┐
monitor-kmu        ├── orchestrator-state ── validator-state ── email [НПА]
monitor-nbu        ┘
```

## Вхід

Останній артефакт з `runs/orchestrator-state/{timestamp}.json` за схемою `shared/schemas/consolidated-artifact.schema.json`.

## Вихід

- `runs/validator-state/{timestamp}.json` — validated artifact за схемою `shared/schemas/validated-artifact.schema.json`
- Email на `legal.monitor.ai@gmail.com` з темою `[НПА] Дайджест моніторингу за {від} — {до}`

## Перевірки per item

| Перевірка | Критерій |
|-----------|----------|
| `url_accessible` | URL повертає HTTP 200 |
| `document_found` | На сторінці ідентифіковано реквізити документа |
| `date_in_period` | Дата публікації потрапляє у розрахунковий period |
| `keywords_match` | Документ відповідає тематиці (ЕДО/КЕП/архів/банк, з урахуванням source_agent_id) |

## Статуси валідації

- **valid** — всі 4 перевірки пройдено, включається до дайджесту
- **invalid** — відхилено (false positive), НЕ включається до дайджесту
- **uncertain** — не вдалось однозначно перевірити, включається до дайджесту з позначкою

## Формат email

Дайджест структурований по трьох секціях: Законопроекти ВРУ / Постанови КМУ / Акти НБУ.
Uncertain items — окрема секція в кінці.

## Розклад

| Час (Київ) | UTC cron | Тригер |
|------------|----------|--------|
| 08:00 | `0 5 * * *` | cron (після orchestrator-state) |
| 17:00 | `0 14 * * *` | cron (після orchestrator-state) |
| За запитом | — | команда «НПА» |

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
