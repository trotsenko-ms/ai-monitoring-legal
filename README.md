# ai-monitoring-legal

**Статус:** PILOT
**Архітектура:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) v2.1
**План імплементації:** [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)

## Про проєкт

ШІ-Агенти для автоматизованого моніторингу змін нормативно-правових актів України.

Система відстежує зміни у законодавстві за двома напрямками:
- **ЕДО** — електронний документообіг, КЕП, архівне зберігання
- **Держоргани** — зареєстровані законопроекти ВРУ, акти КМУ, акти НБУ

## Структура репозиторію

```
agents/
  monitors/        4 monitor-агенти (джерела НПА)
  validators/      2 validator-агенти (перевірка результатів)
  orchestrators/   1 orchestrator-агент (координація гілки держорганів)
shared/
  schemas/         JSON-контракти між агентами
  prompts/         Спільні фрагменти промптів
data/
  dedup/           Файли дедуплікації per-agent (TTL 90 днів)
tests/
  fixtures/        Статичні зразки вхідних даних
  cases/           Тест-кейси per-agent з очікуваними результатами
  results/         Результати тестових прогонів
runs/              Фіксація продакшн-запусків per-agent
docs/              Документація проєкту
```

## Агенти

| Агент | Тип | Джерело | Статус |
|-------|-----|---------|--------|
| monitor-edo | Monitor | zakon.rada.gov.ua, kmu.gov.ua, bank.gov.ua | active |
| monitor-rada-bills | Monitor | itd.rada.gov.ua/billinfo/Bills/period | planned |
| monitor-kmu | Monitor | kmu.gov.ua/npasearch | planned |
| monitor-nbu | Monitor | bank.gov.ua/ua/legislation | planned |
| orchestrator-state | Orchestrator | — | planned |
| validator-edo | Validator | — | planned |
| validator-state | Validator | — | planned |

## Розклад запусків

| Час (Київ) | Гілка | Тригер |
|-----------|-------|--------|
| 08:00 | Держоргани (rada-bills + kmu + nbu → orchestrator → validator) | cron |
| 08:30 | ЕДО (monitor-edo → validator-edo) | cron |
| 17:00 | Держоргани | cron |
| За запитом | ЕДО | команда «ЕДО» |
| За запитом | Держоргани | команда «НПА» |

## Доставка

Email-дайджести надходять на: `legal.monitor.ai@gmail.com`

Типовий день: 3 листи (08:00 держоргани → 08:30 ЕДО → 17:00 держоргани).

## Посилання

- [Архітектура системи](docs/ARCHITECTURE.md)
- [План імплементації](docs/IMPLEMENTATION.md)
- [Журнал змін](docs/CHANGELOG.md)
