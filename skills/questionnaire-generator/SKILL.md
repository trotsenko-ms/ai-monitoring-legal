---
name: questionnaire-generator
description: Generate interactive questionnaires for clarifying project requirements. Use this skill whenever you need to ask follow-up questions about architecture, technical decisions, data structures, or business rules. The skill produces an interactive HTML form with radio buttons, checkboxes, and text fields—optimized for efficiency and excluding vague or redundant questions. Trigger this skill when you have a list of clarification questions (typically 3-7 focused questions) and need them presented in a consistent, professional format that the user can fill and export.
---

# Questionnaire Generator Skill

A system for creating interactive clarification forms that maintain consistency across project phases and prevent circular questioning.

---

## When to Use This Skill

**Use this skill when you need to:**
- Clarify technical architecture decisions
- Understand data structure requirements
- Capture business rules or constraints
- Define process workflows or triggers
- Map sources, templates, or external systems

**DO NOT use when:**
- Asking vague, open-ended questions ("What else?", "Any thoughts?")
- Requesting subjective opinions without context
- Duplicating questions already answered in previous sessions
- You have fewer than 3 or more than 8 questions

---

## Skill Input Format

Call this skill with a JSON structure containing questions and their types:

```json
{
  "title": "ТЗ: Агент моніторингу ВРУ — Уточнення (Раунд 2)",
  "description": "Уточнення архітектури на основі первинного ТЗ",
  "questions": [
    {
      "id": "q1",
      "question": "Карта джерел по темі електронного документообігу — які саме суб'єкти влади?",
      "type": "options",
      "options": [
        { "value": "vru-only", "label": "Лише ВРУ (закони)" },
        { "value": "vru-kmu", "label": "ВРУ + КМУ" },
        { "value": "multi", "label": "ВРУ + КМУ + мін-ва + регулятори" },
        { "value": "custom", "label": "Своя комбінація:" }
      ],
      "allowComment": true
    },
    {
      "id": "q2",
      "question": "Рівень 1 — що надсилати в листі?",
      "type": "checkboxes",
      "options": [
        { "value": "title", "label": "Заголовок НПА" },
        { "value": "link", "label": "Посилання" },
        { "value": "date", "label": "Дата" },
        { "value": "status", "label": "Статус" },
        { "value": "preview", "label": "Попередній анліз (одна фраза)" }
      ],
      "allowComment": true
    },
    {
      "id": "q3",
      "question": "Рівень 2 — хто дає погодження на поглиблений аналіз?",
      "type": "text",
      "placeholder": "Ви вручну? Критерії агента? Комбінація?",
      "allowComment": false
    }
  ]
}
```

---

## Question Types

### 1. **options** (radio buttons)
Single choice. Use for mutually exclusive decisions.

```json
{
  "type": "options",
  "options": [
    { "value": "id", "label": "Display label" }
  ],
  "allowComment": true
}
```

### 2. **checkboxes** (multiple choice)
Multiple selections. Use for feature lists, delivery channels, etc.

```json
{
  "type": "checkboxes",
  "options": [
    { "value": "id", "label": "Display label" }
  ],
  "allowComment": true
}
```

### 3. **text** (text input / textarea)
Open-ended response. Use for detailed explanations, maps, templates.

```json
{
  "type": "text",
  "placeholder": "Hint text...",
  "allowComment": false
}
```

### 4. **table** (structured data)
Key-value pairs. Use for mapping (e.g., sources, templates).

```json
{
  "type": "table",
  "columns": ["Source Name", "URL", "Priority"],
  "allowComment": true
}
```

---

## Output Format

The generated HTML form provides:
- Interactive input fields (radio, checkbox, text, table)
- Export buttons: JSON, copy to clipboard, send to chat
- Professional styling consistent with Claude.ai

User fills the form and chooses export method. Claude receives JSON response with all answers.

---

## Quality Checklist Before Generation

Before calling this skill, verify:

- [ ] **No circular questions** — each Q addresses a different aspect
- [ ] **No vague phrasing** — every Q has concrete expected answers
- [ ] **No duplicates** — compare against previous ТЗ / responses
- [ ] **Focused scope** — 3-7 questions max
- [ ] **Actionable answers** — responses directly inform architecture decisions
- [ ] **Option clarity** — each option is distinct and mutually exclusive (for `options` type)

If any checkbox fails → rewrite those questions before generation.

---

## Examples

### Example 1: Architecture Clarification

**Scenario:** ТЗ received, need to clarify 3-level processing workflow.

Input:
```json
{
  "title": "Уточнення архітектури агента моніторингу",
  "description": "Рівні обробки НПА",
  "questions": [
    {
      "id": "level1",
      "question": "Рівень 1 — що надсилати в листі?",
      "type": "checkboxes",
      "options": [
        { "value": "title", "label": "Заголовок" },
        { "value": "link", "label": "Посилання" }
      ],
      "allowComment": true
    }
  ]
}
```

Output: Interactive form → user selects checkboxes → exports JSON → Claude processes

---

### Example 2: Source Mapping

**Scenario:** Need detailed map of legislative sources.

Input:
```json
{
  "questions": [
    {
      "id": "sources",
      "question": "Карта джерел по темі електронного документообігу",
      "type": "table",
      "columns": ["Назва джерела", "URL", "Статус"],
      "allowComment": true
    }
  ]
}
```

Output: Table with editable rows → user fills → exports as structured data

---

## Integration with Project Workflow

**Phase 1: Initial ТЗ** (already done)
- User fills questionnaire (previous format)
- Claude analyzes, identifies gaps

**Phase 2: Clarification Rounds** (use THIS skill)
1. Claude formulates 3-7 focused questions
2. Calls `questionnaire-generator` with questions
3. User fills interactive form
4. Claude processes JSON response → architecture draft

**Phase 3: Architecture Finalization**
- Claude presents agent architecture diagram
- User reviews, provides feedback
- System prompt drafted

---

## Technical Notes

- Form renders in Claude.ai chat (no external dependencies)
- Styling uses CSS variables (automatic light/dark mode)
- Export formats: JSON, plaintext (clipboard), sendPrompt() to chat
- Mobile-friendly: responsive table layout

---

## When to Avoid This Skill

❌ Single clarification question → ask directly in chat
❌ Feedback on draft code/document → use inline review instead
❌ Questions requiring research → use web_search or document tools first
❌ Vague follow-ups → refine in chat before calling skill

---

## See Also

- Questionnaire storage/versioning → Google Drive / GitHub
- Related: `doc-coauthoring` (for structured document workflows)
- Feedback loops → inline in chat after form completion
