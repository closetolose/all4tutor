# Задача: Этап 5 — Система подтверждения оплат

**План:** `docs/plan.md`, этап 5 (комплексное обновление).

## Чек-лист

- [ ] **5.1** Модель `PaymentReceipt`: student (FK), tutor (FK), amount (Decimal), receipt_date (Date), file (FileField), status (pending/approved/rejected), created_at, reviewed_at (null). Валидаторы: размер файла (например 10 МБ), типы (image/*, application/pdf). Миграция.
- [ ] **5.2** Форма отправки чека для ученика: выбор репетитора (из подтверждённых связей), сумма, дата платежа, файл, опционально комментарий. Размещение: в tutor_card или раздел «Мои оплаты». POST создаёт PaymentReceipt (status=pending).
- [ ] **5.3** Раздел для репетитора «Заявки на пополнение» (или блок в finances): список заявок со статусом pending. Для каждой: ученик, сумма, дата, ссылка на скачивание/превью скана.
- [ ] **5.4** View «Подтвердить»: в `transaction.atomic()` — receipt.status='approved', reviewed_at=now; get_or_create StudentBalance(tutor, student), balance += amount; Transaction.objects.create(deposit); save все изменения.
- [ ] **5.5** View «Отклонить»: receipt.status='rejected', reviewed_at=now; save. Баланс и транзакции не меняются.
- [ ] **5.6** Проверка прав: только репетитор этого чека может подтверждать/отклонять; только ученик с подтверждённой связью может отправлять чек этому репетитору.
- [ ] **5.7** (Опционально) Уведомление репетитора при новой заявке (например через существующий send_telegram_notification).

## Ссылки

- ТЗ: `docs/tz.md` (UC-01, UC-02)
- Архитектура: `docs/architecture.md` (§ 1.1, § 2)
- План: `docs/plan.md` (этап 5)
- Результат анализа: `result_1.md`
