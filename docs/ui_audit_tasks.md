# UI/UX Audit — Конкретные задачи по пунктам

Задачи сформулированы по плану `docs/ui_audit_plan.md`. Выполнять **по порядку батчей**; после каждого батча — проверка Verifier по четырём критериям (375px без горизонтального скролла; кнопки/инпуты ≥ 44px; font-size в input ≥ 16px; gap/margin между блоками).

---

## Фаза 1 — Аудит (сбор проблем)

| # | Задача | Экраны | Результат |
|---|--------|--------|-----------|
| 1.1 | Проверить все экраны на горизонтальный скролл при 375px | Все из карты | Зафиксировать экраны с overflow |
| 1.2 | Проверить отступы: прилипание к краям, отсутствие padding 16px на мобильном | Все | Список экранов с проблемами |
| 1.3 | Замерить размеры кнопок и ссылок (touch targets < 44px) | Все с интерактивом | Список элементов |
| 1.4 | Выявить неконсистентные стили (разные кнопки, шрифты, отступы) | Все | Краткий отчёт |
| 1.5 | Проверить Add lesson: наличие `core/add_lesson.html` или исправить view | Add lesson | Либо создать шаблон, либо поправить view |

**Deliverable:** Секция «Phase 1 – Audit results» в `docs/ui_audit_plan.md` или файл `docs/ui_audit_findings.md`.

---

## Фаза 2 — Layout (сетка и контейнеры)

| # | Задача | Файлы/экраны | Критерий |
|---|--------|---------------|----------|
| 2.1 | Ввести глобальный контейнер: класс `.main-content` или обёртка с `max-width: 1200px; margin: 0 auto;` для десктопа | `base.html`, `style.css` | Контент не растягивается на больших экранах |
| 2.2 | Добавить безопасные зоны на мобильном: `padding: 0 16px` для основного контента при `max-width: 768px` | `style.css`, при необходимости base/mobile base | Контент не касается краёв на 375px |
| 2.3 | Все таблицы обернуть в `.table-container` с `overflow-x: auto` (где ещё не обёрнуты) | Index, Finances, Student card, Group card, Payment receipts, Results, My students, Files, и др. | На 375px таблицы скроллятся вбок, нет горизонтального скролла body |
| 2.4 | Убедиться, что длинные слова/URL не ломают ширину: `word-break: break-word` или `overflow-wrap: break-word` где нужно | Глобально или проблемные блоки | Нет overflow по ширине из-за текста |

**Порядок экранов для 2.1–2.4:** Base/shell → Auth → Index, My students, My tutors, Student card, Tutor card, Group card → формы и таблицы (Edit profile, Confirmations, Add student, Groups, Lessons, Finances, Files, Payment receipts, My assignments, Results, My subjects, Archived, Confirm archive) → FAQ, 404, 500.

---

## Фаза 3 — Компоненты (кнопки, формы, навигация)

| # | Задача | Где | Критерий |
|---|--------|-----|----------|
| 3.1 | Кнопки: единые классы `.btn`, `.btn-primary`, `.btn-outline`, `.btn-danger`; на мобильном `min-height: 48px` | `style.css`, при необходимости шаблоны | Все кнопки ≥ 48px на 375px, есть :hover/:active |
| 3.2 | Инпуты и textarea: `font-size: 16px` минимум, единые border-radius, padding, цвет фокуса | `style.css` (классы .filter-select, .date-input, input, textarea) | Нет зума iOS; единый вид |
| 3.3 | Десктоп: сайдбар и контент не перекрываются, логичные отступы | `base.html`, `style.css` | Проверка на 1440px |
| 3.4 | Мобильный: меню в гамбургере или нижняя навигация; область вызова удобна для большого пальца | `mobile/base.html`, `style.css` | Меню открывается, кнопки ≥ 44px |

**Порядок:** те же экраны, что в Фазе 2; при необходимости общие компоненты (кнопки, инпуты) правятся глобально в CSS.

---

## Фаза 4 — Типографика и отступы (4px grid)

| # | Задача | Где | Критерий |
|---|--------|-----|----------|
| 4.1 | Заголовки: единые размеры h1, h2, h3 в `:root` или в общих классах; на мобильном чуть мельче через @media | `style.css` | Иерархия читаема на 1440px и 375px |
| 4.2 | Вычистить отступы: заменить 13px, 17px и т.п. на кратные 4 (8, 12, 16, 20, 24, 32px) | `style.css`, при необходимости шаблоны | Нет «магических» значений |
| 4.3 | Между карточками и секциями: единообразно `gap` или `margin` (8px, 16px, 24px) | Все экраны с карточками/списками | Verifier: нет «прилипшего» контента |

---

## Батчи для передачи Implementer + Verifier

**Батч 1 (база и авторизация)**  
- Задачи: 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2 — применить к **Base, Auth base, Login, Register**, остальным экранам авторизации (registration_pending, activation_invalid, password reset).  
- Verifier: проверить эти экраны на 1440px и 375px по четырём критериям.

**Батч 2 (главные и ученики/репетиторы)**  
- Задачи 2.3, 2.4, 3.1, 3.2, 4.2, 4.3 — применить к **Index, FAQ, My students, Archived students, Student card, Add student, My tutors, Tutor card, Confirm archive**.  
- Verifier: те же критерии.

**Батч 3 (группы и занятия)**  
- Те же задачи — **Group card, Edit group, Create group, Add lesson, Edit lesson, Homework detail**.  
- Проверить/добавить `core/add_lesson.html` при необходимости (задача 1.5).  
- Verifier: те же критерии.

**Батч 4 (финансы, файлы, задания, профиль)**  
- Те же задачи — **Finances, Payment receipts (student & tutor), Files library, My assignments, Results, Edit profile, Confirmations, My subjects**.  
- Verifier: те же критерии.

**Батч 5 (ошибки и полировка)**  
- **404, 500**, глобальная проверка 4px grid и переменных.  
- Verifier: финальный проход по всем экранам, заполнение таблицы чекпоинтов в `ui_audit_plan.md`.

---

## Критерии приёмки Verifier (напоминание)

1. **Mobile:** при 375px нет горизонтального скролла страницы → иначе REJECT.  
2. **Touch:** высота кнопок и инпутов ≥ 44px → иначе REJECT.  
3. **Zoom:** font-size в `<input>` ≥ 16px → иначе REJECT.  
4. **Visual:** между карточками/секциями есть gap или margin → иначе REJECT.

После каждого батча обновлять таблицу в разделе 3 плана (`ui_audit_plan.md`).
