# Задача: Этап 1 — Model & Admin

**План:** `docs/plan.md`, этап 1.

## Чек-лист

- [ ] **1.1** В `core/models.py` в модель `ConnectionRequest` добавить поле `color_hex = models.CharField(max_length=7, null=True, blank=True)`. Создать и применить миграцию.
- [ ] **1.2** В `core/models.py` добавить модель `UserGroupColor` (user FK → Users, group FK → StudyGroups, color_hex CharField(7), unique_together (user, group)). Создать и применить миграцию.
- [ ] **1.3** В `core/admin.py` зарегистрировать/обновить: ConnectionRequest — отобразить `color_hex` в list_display; зарегистрировать UserGroupColor с list_display (user, group, color_hex).
- [ ] **1.4** (Опционально) В модели или в формах валидация формата #RRGGBB для непустого color_hex.

## Ссылки

- Архитектура: `docs/architecture.md` (§ 1)
- ТЗ: `color-indicator/tz.md`
