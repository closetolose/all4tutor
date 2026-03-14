# ТЗ: Задача 3.1 — Хелпер создания уведомлений

**Источник:** notification_plan.md, раздел 3.1.

**Цель:** Единая точка создания in-app уведомлений и опциональная отправка в Telegram.

## Требования

1. **Функция `notify_user`**
   - Размещение: `core/utils.py` (в этом же файле уже есть `send_telegram_notification`).
   - Сигнатура: `notify_user(user, message, link=None, notification_type='info', send_telegram=False)`.
   - Параметры:
     - `user` — экземпляр `User` (Django AUTH_USER_MODEL), не Profile.
     - `message` — строка, текст уведомления (до 255 символов, модель Notification.message).
     - `link` — строка или None; при None сохранять пустую строку или null в поле Notification.link.
     - `notification_type` — строка, одна из допустимых для Notification.type (по умолчанию 'info'); в модели есть choices: 'warning', 'info'.
     - `send_telegram` — bool, по умолчанию False. Если True и у user есть profile с telegram_id — после создания Notification вызвать `send_telegram_notification(user.profile, message)`.
   - Действие: создать одну запись `Notification` с полями user, message, link (или ''), type=notification_type, is_read=False. Без создания лишних записей и без изменения других моделей.

2. **Рефакторинг существующего кода**
   - В `core/management/commands/check_overdue_homeworks.py` заменить прямой вызов `Notification.objects.create(...)` на вызов `notify_user(hw.student.user, message, link=link, notification_type='warning')`. Импорт: из `core.utils` импортировать `notify_user`; модель `Notification` в этой команде больше не импортировать (если не используется в других местах команды).

## Ограничения

- Не менять модель `Notification` (поля, миграции).
- Не добавлять новые URL/вьюхи.
- Проект: Django (Python), не PHP.

## Критерий приёмки

- В `core/utils.py` присутствует функция `notify_user`, удовлетворяющая требованиям выше.
- Команда `check_overdue_homeworks` создаёт уведомления через `notify_user`; поведение (создание уведомления ученику при просрочке ДЗ) сохраняется.
