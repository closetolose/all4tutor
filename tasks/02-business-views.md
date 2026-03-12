# Задача: Этап 2 — Business Logic & Views

**План:** `docs/plan.md`, этап 2.

## Чек-лист

- [ ] **2.1** В view `index`: для ученика построить словари `tutor_colors` (ConnectionRequest по student=user) и `group_colors` (UserGroupColor по user); для репетитора — только `group_colors`. Передать в контекст.
- [ ] **2.2** В view `index`: для каждого урока вычислить `display_color` (из group_colors или tutor_colors по роли). Передать в контекст `lesson_colors` = {lesson.id: hex or None} или атрибут на объектах.
- [ ] **2.3** В view `load_more_lessons`: при рендере `lessons_rows.html` передавать те же `lesson_colors` (или пересчитать для переданного среза lessons) и role.
- [ ] **2.4** В view `my_assignments`: для ученика загрузить `tutor_colors` по ConnectionRequest; передать в контекст (в шаблоне брать цвет по hw.tutor_id).
- [ ] **2.5** Создать view `update_tutor_color` (POST, connection_id): проверка connection.student == request.user.profile; обновить color_hex; сохранить. URL и имя маршрута.
- [ ] **2.6** Создать view `update_group_color` (POST, group_id): проверка доступа (репетитор — владелец, ученик — в группе); get_or_create UserGroupColor; обновить color_hex. URL и имя маршрута.

## Ссылки

- Архитектура: `docs/architecture.md` (§ 2)
- План: `docs/plan.md` (этап 2)
