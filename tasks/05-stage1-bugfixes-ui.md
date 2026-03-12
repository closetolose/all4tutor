# Задача: Этап 1 — Багфиксы и мелкий UI

**План:** `docs/plan.md`, этап 1 (комплексное обновление).

## Чек-лист

- [ ] **1.1** Убрать inline `onmouseover`/`onmouseout` со строк таблицы уроков в `core/index.html` (и при необходимости в `core/lessons_rows.html`).
- [ ] **1.2** В `static/css/style.css`: правило `.entity-color-indicator:hover` с фоном через `color-mix(in srgb, var(--custom-entity-color, transparent) 18%, transparent)` (или 20%). Учесть `[data-theme="dark"]`.
- [ ] **1.3** Исключить перебивание фона: `tbody tr:hover` не применять к строкам с индикатором — использовать `tbody tr:not(.entity-color-indicator):hover` или более специфичное правило для `.entity-color-indicator:hover`.
- [ ] **1.4** В `core/templates/mobile/base.html` (или общем блоке стилей mobile): то же правило `.entity-color-indicator:hover` при наличии цветовых индикаторов на mobile.
- [ ] **1.5** В модель `ConnectionRequest` добавить поле `tutor_color_hex` (CharField max_length=7, null=True, blank=True). Миграция.
- [ ] **1.6** В карточке ученика (`student_card`, core и mobile) для репетитора: блок «Цветовая метка (ваш цвет)» с палитрой и формой POST на обновление `tutor_color_hex` (новый view или расширение существующего).
- [ ] **1.7** В view `index` и `load_more_lessons` для репетитора: при индивидуальном уроке (без группы) брать цвет из `ConnectionRequest` (tutor=user, student=lesson.student) — поле `tutor_color_hex`; при группе — как сейчас из `UserGroupColor`.
- [ ] **1.8** В карточке ученика (`student_card`, core и mobile): блок «Группы» — список `StudyGroups`, в которых состоит ученик (фильтр по tutor=текущий репетитор), со ссылками на `group_card`.

## Ссылки

- ТЗ: `docs/tz.md` (UC-06, UC-08)
- Архитектура: `docs/architecture.md` (§ 3.3, 3.4)
- План: `docs/plan.md` (этап 1)
- Результат анализа: `result_1.md`
