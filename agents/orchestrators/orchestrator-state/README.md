# orchestrator-state

**Версія:** 1.0
**Тип:** Orchestrator
**Модель:** claude-sonnet-4-5

## Призначення

Координатор гілки держорганів. Збирає артефакти трьох monitor-агентів і передає єдиний консолідований артефакт до validator-state.

## Місце в pipeline

```
monitor-rada-bills ┐
monitor-kmu        ├── orchestrator-state ── validator-state ── email
monitor-nbu        ┘
```

## Вхід

Три JSON-артефакти (останній за timestamp у кожній директорії):
- `runs/monitor-rada-bills/{timestamp}.json`
- `runs/monitor-kmu/{timestamp}.json`
- `runs/monitor-nbu/{timestamp}.json`

## Вихід

`runs/orchestrator-state/{timestamp}.json` — консолідований артефакт за схемою `shared/schemas/consolidated-artifact.schema.json`.

## Розклад

| Час (Київ) | UTC cron | Тригер |
|------------|----------|--------|
| 08:00 | `0 5 * * *` | cron |
| 17:00 | `0 14 * * *` | cron |
| За запитом | — | команда «НПА» |

## Помилки

- Якщо один монітор недоступний — консолідується без нього, агент фіксується в `stats.sources_with_errors`
- Якщо всі три монітори недоступні — артефакт НЕ зберігається, pipeline зупиняється

## Файли

| Файл | Опис |
|------|------|
| `prompt.md` | System prompt агента |
| `config.json` | Параметри запуску |
| `README.md` | Цей документ |
