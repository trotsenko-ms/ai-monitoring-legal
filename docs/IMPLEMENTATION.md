# Імплементація пілоту: план дій

**Версія:** 1.0
**Дата:** 06.05.2026
**Статус:** READY TO START
**Repo:** https://github.com/trotsenko-ms/ai-monitoring-legal
**Архітектура:** docs/ARCHITECTURE.md v2.1

> Цей документ — покроковий план впровадження. Кожен етап виконується послідовно.
> Виконувати в Claude Code, якщо не вказано інше.
> Позначати виконані задачі: `[x]`.

---

## ФАЗА 1 — Структура репозиторію

**Мета:** привести repo у відповідність до ARCHITECTURE.md v2.1.
**Залежності:** немає.

### 1.1 Створити папки (якщо не існують)

```
agents/monitors/monitor-edo/
agents/monitors/monitor-rada-bills/
agents/monitors/monitor-kmu/
agents/monitors/monitor-nbu/
agents/validators/validator-edo/
agents/validators/validator-state/
agents/orchestrators/orchestrator-state/
shared/schemas/
shared/prompts/
data/dedup/
tests/fixtures/
tests/cases/
tests/results/
runs/monitor-edo/
runs/monitor-rada-bills/
runs/monitor-kmu/
runs/monitor-nbu/
runs/validator-edo/
runs/validator-state/
runs/orchestrator-state/
docs/agents/
```

- [ ] Створити всі папки вище, в кожну порожню папку покласти `.gitkeep`

### 1.2 Міграція існуючого агента

- [ ] Скопіювати `agents/npa-monitor-agent.md` → `agents/monitors/monitor-edo/prompt.md`
- [ ] Створити `agents/monitors/monitor-edo/README.md` — короткий опис агента (1 сторінка)
- [ ] Стару папку/файл `agents/npa-monitor-agent.md` — **не видаляти** до успішного першого тесту monitor-edo

### 1.3 Оновити структуру data/

- [ ] Перемістити `data/seen_urls.json` → `data/dedup/seen_urls_edo.json`
- [ ] Оновити вміст файлу: додати поля `agent_id: "monitor-edo"` та `last_updated`
- [ ] Створити порожні файли:
  - `data/dedup/seen_urls_rada_bills.json` — `{ "agent_id": "monitor-rada-bills", "last_updated": "", "urls": [] }`
  - `data/dedup/seen_urls_kmu.json`
  - `data/dedup/seen_urls_nbu.json`

### 1.4 Документація

- [ ] Перемістити або оновити `docs/ARCHITECTURE.md` — замінити на версію 2.1
- [ ] Створити `docs/CHANGELOG.md` з записами v1.0 → v2.0 → v2.1 (з ARCHITECTURE.md секція 15)
- [ ] Оновити `README.md` кореня repo — відобразити нову структуру та статус PILOT

### 1.5 Commit

- [ ] Commit з повідомленням: `feat: repo structure v2.1 — multi-agent pilot`

---

## ФАЗА 2 — System prompts агентів-моніторів

**Мета:** створити інструкції для 4 Monitor-агентів.
**Залежності:** Фаза 1 завершена.

> Кожен агент = папка з трьома файлами: `prompt.md` (system prompt), `config.json` (параметри), `README.md` (опис).

### 2.1 monitor-edo (міграція + адаптація)

- [ ] Адаптувати `agents/monitors/monitor-edo/prompt.md`:
  - Оновити Крок 0 (дедуплікація): шлях змінено на `data/dedup/seen_urls_edo.json`
  - Оновити формат seen_urls: додати поле `agent_id`
  - Додати секцію **OUTPUT**: агент зберігає результат у `runs/monitor-edo/{timestamp}.json` за JSON-контрактом (схема в `shared/schemas/monitor-artifact.schema.json`)
  - Версія: 1.0 (перша версія в новій архітектурі)
- [ ] Створити `agents/monitors/monitor-edo/config.json`
- [ ] Commit: `feat: monitor-edo prompt v1.0`

### 2.2 monitor-rada-bills (новий)

**Джерело:** `https://itd.rada.gov.ua/billinfo/Bills/period`
**Що шукає:** зареєстровані законопроекти за вказаний період

- [ ] Створити `agents/monitors/monitor-rada-bills/prompt.md`:
  - Роль: Monitor зареєстрованих законопроектів ВРУ
  - Крок 0: дедуплікація через `data/dedup/seen_urls_rada_bills.json`
  - Крок 1: завантажити сторінку `itd.rada.gov.ua/billinfo/Bills/period`, отримати список законопроектів за поточний розрахунковий період
  - Крок 2: фільтрація дублів
  - Крок 3: валідація (відповідність тематиці: ЕДО, КЕП, архівне зберігання, банківський документообіг)
  - Output: JSON-артефакт за контрактом → `runs/monitor-rada-bills/{timestamp}.json`
- [ ] Створити `config.json`, `README.md`
- [ ] Commit: `feat: monitor-rada-bills prompt v1.0`

### 2.3 monitor-kmu (новий)

**Джерело:** `https://www.kmu.gov.ua/npasearch`
**Що шукає:** опубліковані постанови та розпорядження КМУ за вказаний період

- [ ] Створити `agents/monitors/monitor-kmu/prompt.md` — аналогічна структура до 2.2, джерело і логіка парсингу відповідають kmu.gov.ua/npasearch
- [ ] Створити `config.json`, `README.md`
- [ ] Commit: `feat: monitor-kmu prompt v1.0`

### 2.4 monitor-nbu (новий)

**Джерело:** `https://bank.gov.ua/ua/legislation`
**Що шукає:** опубліковані нормативні акти НБУ

- [ ] Створити `agents/monitors/monitor-nbu/prompt.md` — аналогічна структура, джерело bank.gov.ua/ua/legislation
- [ ] Створити `config.json`, `README.md`
- [ ] Commit: `feat: monitor-nbu prompt v1.0`

---

## ФАЗА 3 — JSON-схеми та shared

**Мета:** зафіксувати контракти між агентами.
**Залежності:** Фаза 2 (щоб схеми відповідали реальним промптам).

- [ ] Створити `shared/schemas/monitor-artifact.schema.json` — схема виходу кожного Monitor:
  ```json
  { "agent_id", "agent_version", "run_id", "period": { "from", "to" }, "source_url", "items": [ { "title", "number", "date_published", "url", "raw_status" } ], "stats": { "items_found", "duplicates_filtered", "errors" } }
  ```
- [ ] Створити `shared/schemas/consolidated-artifact.schema.json` — схема виходу orchestrator-state (масив з 3 monitor artifacts)
- [ ] Створити `shared/schemas/validated-artifact.schema.json` — схема виходу Validator (items + validation_status per item)
- [ ] Commit: `feat: JSON schemas for agent contracts`

---

## ФАЗА 4 — Orchestrator та Validators

**Мета:** створити інструкції для координатора і валідаторів.
**Залежності:** Фаза 3 завершена (схеми мають бути готові).

### 4.1 orchestrator-state

- [ ] Створити `agents/orchestrators/orchestrator-state/prompt.md`:
  - Читає три артефакти з `runs/monitor-rada-bills/`, `runs/monitor-kmu/`, `runs/monitor-nbu/` (останній за timestamp)
  - Об'єднує в consolidated artifact за схемою `shared/schemas/consolidated-artifact.schema.json`
  - Зберігає у `runs/orchestrator-state/{timestamp}.json`
- [ ] Commit: `feat: orchestrator-state prompt v1.0`

### 4.2 validator-edo

- [ ] Створити `agents/validators/validator-edo/prompt.md` (модель: Haiku):
  - Читає останній артефакт з `runs/monitor-edo/`
  - Для кожного item перевіряє: доступність URL, наявність документа, дата публікації в межах розрахункового періоду, відповідність ключовим словам
  - Зберігає validated artifact у `runs/validator-edo/{timestamp}.json`
  - Формує email-дайджест і надсилає на `legal.monitor.ai@gmail.com`
- [ ] Commit: `feat: validator-edo prompt v1.0`

### 4.3 validator-state

- [ ] Створити `agents/validators/validator-state/prompt.md` (модель: Haiku):
  - Аналогічна логіка, читає з `runs/orchestrator-state/`
  - Зберігає у `runs/validator-state/{timestamp}.json`
  - Формує email-дайджест і надсилає на `legal.monitor.ai@gmail.com`
- [ ] Commit: `feat: validator-state prompt v1.0`

---

## ФАЗА 5 — Email-скринька

**Мета:** підготувати скриньку для отримання дайджестів.
**Виконується вручну, поза Claude Code.**

- [ ] Створити Gmail-акаунт: `legal.monitor.ai@gmail.com`
- [ ] Увімкнути отримання листів від сервісів (переконатися що не потрапляє в спам)
- [ ] Зафіксувати облікові дані у безпечному місці (не в repo)

---

## ФАЗА 6 — GitHub Actions (cron)

**Мета:** автоматизувати запуски за розкладом.
**Залежності:** Фази 1-4 завершені та протестовані вручну.

- [ ] Створити `.github/workflows/monitor-state.yml`:
  ```yaml
  # Тригери: cron 08:00 + 17:00 Київ (UTC+3 = 05:00 + 14:00 UTC)
  # + workflow_dispatch (manual trigger з input "НПА")
  # Запускає: orchestrator-state → validator-state → email
  ```
- [ ] Створити `.github/workflows/monitor-edo.yml`:
  ```yaml
  # Тригер: cron 08:30 Київ (05:30 UTC)
  # + workflow_dispatch (manual trigger з input "ЕДО")
  # Запускає: monitor-edo → validator-edo → email
  ```
- [ ] Перевірити роботу GitHub Actions: ручний запуск кожного workflow
- [ ] Commit: `feat: GitHub Actions workflows for cron scheduling`

---

## ФАЗА 7 — Індивідуальне тестування агентів

**Мета:** перевірити кожного агента ізольовано перед інтеграцією.
**Залежності:** Фази 1-4.

- [ ] Тест monitor-edo: запустити вручну, перевірити output в `runs/monitor-edo/`
- [ ] Тест monitor-rada-bills: аналогічно
- [ ] Тест monitor-kmu
- [ ] Тест monitor-nbu
- [ ] Тест orchestrator-state: запустити з реальними артефактами з Фази вище
- [ ] Тест validator-edo: перевірити що email надходить на `legal.monitor.ai@gmail.com`
- [ ] Тест validator-state: аналогічно
- [ ] Зберегти тестові артефакти у `tests/fixtures/` для подальшого регресійного тестування

---

## ФАЗА 8 — Інтеграційне тестування

**Мета:** перевірити повний pipeline від тригера до email.
**Залежності:** Фаза 7 — всі агенти окремо пройшли тест.

- [ ] Запустити повний pipeline гілки ЕДО вручну (команда «ЕДО»): monitor-edo → validator-edo → email
- [ ] Запустити повний pipeline гілки Держоргани (команда «НПА»): 3 monitors → orchestrator → validator → email
- [ ] Перевірити: коректний формат листів, правильний заголовок, правильний період
- [ ] Перевірити дедуплікацію: повторний запуск через хвилину — ті самі URL не дублюються в дайджесті
- [ ] Зафіксувати результати у `tests/results/integration-test-{date}.md`

---

## ФАЗА 9 — Продакшн-запуск

**Мета:** активувати cron і розпочати 30-денний пілот.
**Залежності:** Фаза 8 завершена успішно.
**Статус:** LAUNCHED 2026-05-07

- [x] Переконатися що GitHub Actions workflows активні (not disabled)
  - `monitor-state.yml` — cron `0 5 * * *` (08:00 Kyiv) та `0 14 * * *` (17:00 Kyiv) — ACTIVE on main
  - `monitor-edo.yml` — cron `30 5 * * *` (08:30 Kyiv) — ACTIVE on main
  - Обидва workflows мають `workflow_dispatch` для ручного тригера
- [ ] Дочекатися першого автоматичного cron-запуску о 08:00 або 08:30
- [ ] Перевірити email — лист отримано, формат коректний
- [ ] Протягом першого тижня: щоденно переглядати `runs/` для виявлення аномалій
  - Інструкція: `docs/MONITORING-RUNBOOK.md`
- [ ] Після 30 днів: оцінити метрики (precision, recall, стабільність) → рішення про фазу 2

---

## ДОВІДКА: порядок відкриття сесії в Claude Code

На початку кожної сесії в Claude Code давати такий контекст:

```
Проєкт: ai-monitoring-legal (GitHub: trotsenko-ms/ai-monitoring-legal)
Архітектура: docs/ARCHITECTURE.md v2.1
Поточний план: docs/IMPLEMENTATION.md
Поточний статус: [вказати яка фаза виконується]
Задача на цю сесію: [конкретна задача з чеклисту]
```

---

## Відкриті питання імплементації

1. Механізм відправки email з агента — через Gmail API або SMTP? Уточнити під час Фази 4.
2. Зберігання credentials для Gmail — GitHub Secrets (рекомендовано).
3. Як саме Claude Code тригерує агентів через GitHub Actions — уточнити під час Фази 6.
