# Задача: Этап 4 — UI Интеграция (применение цвета)

**План:** `docs/plan.md`, этап 4.

## Чек-лист

- [ ] **4.1** В `static/css/style.css` (и при необходимости в mobile): класс `.entity-color-indicator` с `border-left` и `background` на основе `var(--custom-entity-color)`, opacity фона 10–15%. Учесть `[data-theme="dark"]`.
- [ ] **4.2** В `core/lessons_rows.html`: для каждой строки при наличии `display_color` задать на `<tr>` `style="--custom-entity-color: {{ display_color }};"` и класс `entity-color-indicator`.
- [ ] **4.3** В `mobile/index.html`: для каждой `.lesson-card` задать `--custom-entity-color` и класс при наличии цвета.
- [ ] **4.4** В `core/my_assignments.html`: для каждой строки ДЗ — цвет из `tutor_colors` по `hw.tutor_id`, переменная и класс на строке/обёртке.
- [ ] **4.5** В `mobile/my_assignments.html`: то же для карточек ДЗ.
- [ ] **4.6** Проверить отображение в светлой и тёмной теме; контраст текста не пострадал.

## Ссылки

- ТЗ: `color-indicator/tz.md` (UC-02, UC-03, ограничения по читаемости)
- Архитектура: `docs/architecture.md` (§ 3.1–3.4)
- План: `docs/plan.md` (этап 4)
