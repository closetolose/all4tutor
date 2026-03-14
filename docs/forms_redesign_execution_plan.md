# План внедрения редизайна форм (Execution Plan)

На основе документа `forms_ux_ui_audit.md`.

---

## Приоритеты и фазы

| Фаза | Приоритет | Описание |
|------|-----------|----------|
| **1** | Высокий | Design tokens, единые классы полей, стили ошибок, рефакторинг десктопных форм |
| **2** | Средний | Редактирование группы (секции + кнопки), плейсхолдеры и единицы |
| **3** | Низкий | Тост «Сохранено», консистентность мобильной страницы add_lesson |

---

## Фаза 1: Единая система полей и валидация

### 1.1 Design Tokens и глобальные классы (static/css/style.css)

- [ ] **1.1.1** Добавить CSS-переменные для форм (в блок `:root` или рядом с существующими переменными):
  - `--input-height: 44px`
  - `--input-padding: 12px 16px`
  - `--input-radius: var(--radius-md)` или `8px`
  - `--input-border: 1px solid var(--border)`
  - `--space-form-section: 24px` (отступ между секциями)

- [ ] **1.1.2** Класс `.form-input`: применяется к `input[type="text"]`, `input[type="number"]`, `input[type="email"]`, `input[type="date"]`, `input[type="time"]` внутри `.form-group` или глобально для контекста форм. Стили: width 100%, height/ min-height из переменных, padding, border, border-radius, font-size 16px, focus state (border-color primary, outline none, box-shadow).

- [ ] **1.1.3** Классы `.form-select`, `.form-textarea`: аналогично `.form-input` (textarea с resize vertical или none, min-height).

- [ ] **1.1.4** Усилить `.form-label`: убедиться, что стиль единый (display block, font-size 12–14px, font-weight 600, color text-muted, margin-bottom 6–8px). Использовать везде вместо инлайнов.

- [ ] **1.1.5** Класс `.form-section`: margin-bottom `var(--space-form-section)`; дочерний `.form-section-title`: font-size 12px, font-weight 800, color text-muted, text-transform uppercase, letter-spacing 0.5px, margin-bottom 10–12px.

- [ ] **1.1.6** Класс `.form-group`: margin-bottom 20px (или 1.25rem). Внутри: .form-label + input/select/textarea с классами form-input/form-select/form-textarea.

- [ ] **1.1.7** Валидация: класс `.field-error` — блок под полем, font-size 12–13px, color danger-text, margin-top 4–6px. Класс `.is-invalid` для input/select/textarea — border-color danger, при focus сохранять красную обводку или усилить.

### 1.2 Рефакторинг десктопных шаблонов (убрать инлайны, применить классы)

- [ ] **1.2.1** **core/edit_group.html**: обернуть блоки в `.form-section` с заголовком «Основное»; поля названия и предмета — `.form-group` + `.form-label` + добавить класс к полям (form-input/form-select); блок учеников — в той же секции, список чекбоксов оформить без инлайнов. Секция «Цвет группы» — отдельный `.form-section` с заголовком «Цвет группы»; кнопка «Сохранить цвет» — `.btn-outline`. Кнопка «Сохранить группу» — `.btn-primary`, ссылка «Отмена» — класс (например `.btn-outline` или ссылка с классом). Убрать все `style="..."` с лейблов и контейнеров.

- [ ] **1.2.2** **core/add_student.html**: один `.form-group` с `.form-label` и `input.form-input` (name username, placeholder «Например: student123»). Кнопка — `.btn-primary`, ссылка «Вернуться» — без инлайнов (класс ссылки). Сообщения об ошибках/успехе оставить, убрать инлайновые стили с блока сообщений (вынести в класс, например `.form-message`).

- [ ] **1.2.3** **core/create_group.html**: секция без заголовка или с «Основное»; поля название, предмет, ученики — `.form-group` + `.form-label` + классы полей. Контейнер чекбоксов — без инлайнов (класс). Кнопка «Сохранить группу» — `.btn-primary`. Ссылка «Назад» — класс. Подсказка «Сначала добавьте предметы» — класс для текста ошибки/подсказки.

- [ ] **1.2.4** **core/edit_lesson.html**: для каждого поля формы (кроме materials) — `.form-group` + `.form-label` + поле с классом form-input/form-select. Блок материалов оставить, кнопку «Выбрать файлы» — `.btn-outline`. Кнопки: «Сохранить» — `.btn-primary`, «Отмена» — `.btn-outline` (не инлайн background/color).

- [ ] **1.2.5** **core/edit_profile.html**: секция «Основное» (имя, фамилия, отчество, контакты, Telegram ID) — `.form-section` + заголовок; каждый лейбл — `.form-label`, поля — `.form-input`/`.form-select`. Блок «Информация для репетитора» — отдельная `.form-section` с заголовком. Ошибки Telegram ID выводить в `<div class="field-error">`, для поля при ошибке добавить класс `is-invalid` (через шаблон или JS). Кнопка «Сохранить» — `.btn-primary`. Часовой пояс и прочее — без инлайнов.

### 1.3 Вывод ошибок валидации в формах

- [ ] **1.3.1** В шаблонах, где выводятся `form.field.errors`, обернуть вывод в `<div class="field-error">` и добавлять к соответствующему input/select класс `is-invalid` при наличии ошибки (в Django: `{% if field.errors %} {{ field|add_class:'form-input is-invalid' }}` или вручную проверить field.errors и вывести класс). Там, где нет такого вывода, добавить блок для ошибок под полем (edit_group, add_student, create_group, edit_lesson, edit_profile).

---

## Фаза 2: Группа, плейсхолдеры, единицы

### 2.1 Редактирование группы (desktop + mobile)

- [ ] **2.1.1** Desktop: уже заложено в 1.2.1 (две секции, кнопки primary/outline). Проверить, что цветовая палитра использует общий include или классы из дизайн-системы (color-swatch 30px уже есть в проекте).

- [ ] **2.1.2** Mobile (edit_group.html): привести разметку к тем же секциям; кнопки и ссылки — те же классы (eg-submit → можно оставить или заменить на btn-primary для консистентности с глобальными стилями).

### 2.2 Плейсхолдеры и единицы измерения

- [ ] **2.2.1** В формах добавления/редактирования занятия (core/add_lesson.html, mobile index addLessonModal): для поля «Цена» — placeholder «0» или «0 ₽»; «Длительность» — «45» или «45 мин»; «Кол-во недель» — «4» или «4 нед.» (если поле есть). При необходимости добавить текстовый суффикс рядом (например «₽») через разметку, если placeholder недостаточен.

- [ ] **2.2.2** В других формах, где есть число (цена, длительность), добавить placeholder с единицами по тому же принципу.

---

## Фаза 3: Обратная связь и консистентность

### 3.1 Сообщение об успешном сохранении

- [ ] **3.1.1** Вариант A: после успешного POST редирект с query-параметром `?saved=1`; на целевой странице (например my_students, index) вывести вверху баннер «Сохранено» (класс типа `.form-toast` или `.alert-success`), скрывать через 3–5 сек или по клику. Вариант B: на странице формы после submit показать тост (без редиректа) и затем редирект. Реализовать один из вариантов для ключевых форм (edit_group, create_group, edit_profile, add_lesson).

### 3.2 Мобильная страница add_lesson

- [ ] **3.2.1** Либо удалить прямую ссылку на страницу add_lesson (mobile), оставив только модалку; либо привести разметку/классы add_lesson.html к тем же, что в модалке (form-section, row, card), чтобы не было рассинхрона. По решению команды — минимально достаточно документировать, что основной сценарий — модалка.

---

## Чек-лист для Verifier

1. Все пункты из `forms_ux_ui_audit.md` (секция 3 «Редизайн») учтены в коде.
2. Вёрстка адаптивна: на узком экране нет горизонтального скролла; тап-зоны не менее 40px.
3. Визуальная иерархия: секции с заголовками, одна primary-кнопка, вторичные — outline/ссылка.
4. Состояния: focus у полей, .is-invalid при ошибке, .field-error под полем.
5. Нет избыточных инлайновых стилей в перечисленных шаблонах; нет конфликтующих правил в CSS.

---

## Файлы для изменения

| Файл | Задачи |
|------|--------|
| `static/css/style.css` | 1.1 (tokens, .form-input, .form-section, .field-error, .is-invalid) |
| `core/templates/core/edit_group.html` | 1.2.1, 1.3 |
| `core/templates/core/add_student.html` | 1.2.2, 1.3 |
| `core/templates/core/create_group.html` | 1.2.3, 1.3 |
| `core/templates/core/edit_lesson.html` | 1.2.4, 1.3 |
| `core/templates/core/edit_profile.html` | 1.2.5, 1.3 |
| `core/templates/core/add_lesson.html` | 2.2.1 (placeholders) |
| `core/templates/mobile/index.html` | 2.2.1 (addLessonModal placeholders) |
| `core/templates/mobile/edit_group.html` | 2.1.2 (опционально классы) |
| Views (опционально) | 3.1.1 redirect с ?saved=1; отображение баннера в шаблонах списков |
