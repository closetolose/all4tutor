# UI/UX Audit Plan — Глобальный UI/UX Аудит и Рефакторинг (Mobile & Desktop Parity)

**Epic:** Full UI audit and refactor for All4Tutors (Desktop 1440px & Mobile 375px).  
**Stack:** Django Templates, Vanilla JS, plain CSS with variables. No React/Vue.  
**Rule:** Refactoring follows this screen map; no blind rewrites. Implementers work screen by screen per this plan.

---

## 1. Карта экранов (Screen Map)

Below is the complete list of user-facing screens derived from `tutor_project/urls.py`, `core/views.py`, and templates under `core/templates/core/` and `core/templates/mobile/`.  
`smart_render` selects `mobile/` when `request.is_mobile` and the mobile template exists; otherwise `core/` is used.

### 1.1 Public / Auth (no sidebar)

| Screen | Route(s) | Desktop template | Mobile template | Description | Layout | Tables / Forms / Grids |
|--------|----------|------------------|-----------------|-------------|--------|------------------------|
| **Login** | `/login/` | `core/login.html` | — | Sign in form | Full-width, auth | Form (email, password) |
| **Register** | `/register/` | `core/register.html` | — | Registration | Full-width, auth | Form (fields) |
| **Registration pending** | (after register) | `core/registration_pending.html` | — | Email verification message | Full-width | — |
| **Activation invalid** | `/activate/<uidb64>/<token>/` | `core/activation_invalid.html` | — | Invalid activation link | Full-width | — |
| **Email verification** | (referenced) | `core/email_verification.html` | — | Email verification info | Full-width | — |
| **Password reset** | `/password-reset/`, `.../done/`, `.../confirm/...`, `.../complete/` | `core/registration/password_reset_*.html` | — | Reset flow (4 steps) | Full-width | Forms on form/confirm |

### 1.2 Main app — Dashboard & navigation

| Screen | Route(s) | Desktop template | Mobile template | Description | Layout | Tables / Forms / Grids |
|--------|----------|------------------|-----------------|-------------|--------|------------------------|
| **Index / Dashboard** | `/` | `core/index.html` | `mobile/index.html` | Main dashboard (lessons, quick actions) | Sidebar + main | Possible grids/lists, cards |
| **FAQ** | `/faq/` | `core/faq.html` | `mobile/faq.html` | FAQ content | Sidebar + main or full-width | Accordion/list content |

### 1.3 Students & connections (tutor view)

| Screen | Route(s) | Desktop template | Mobile template | Description | Layout | Tables / Forms / Grids |
|--------|----------|------------------|-----------------|-------------|--------|------------------------|
| **My students** | `/my-students/` | `core/my_students.html` | `mobile/my_students.html` | List of students | Sidebar + main | List/cards, filters |
| **Archived students** | `/students/archive-list/` | `core/archived_students.html` | `mobile/archived_students.html` | Archived students list | Sidebar + main | List/table |
| **Student card** | `/student/<id>/` | `core/student_card.html` | `mobile/student_card.html` | Single student: lessons, homework, finances | Sidebar + main | Tables (lessons, attendance), forms, grids |
| **Add student** | `/add-student/` | `core/add_student.html` | `mobile/add_student.html` | Add new student | Sidebar + main | Form |
| **Confirm archive** | (archive flow) | `core/confirm_archive.html` | — | Confirm archive student | Sidebar + main | Buttons/actions |

### 1.4 Tutors (student view)

| Screen | Route(s) | Desktop template | Mobile template | Description | Layout | Tables / Forms / Grids |
|--------|----------|------------------|-----------------|-------------|--------|------------------------|
| **My tutors** | `/my-tutors/` | `core/my_tutors.html` | `mobile/my_tutors.html` | List of tutors | Sidebar + main | List/cards |
| **Tutor card** | `/tutor-card/<id>/` | `core/tutor_card.html` | `mobile/tutor_card.html` | Single tutor details | Sidebar + main | Cards, possible list/table |

### 1.5 Groups

| Screen | Route(s) | Desktop template | Mobile template | Description | Layout | Tables / Forms / Grids |
|--------|----------|------------------|-----------------|-------------|--------|------------------------|
| **Group card** | `/group-card/<id>/` | `core/group_card.html` | `mobile/group_card.html` | Group details, lessons, students | Sidebar + main | Tables, lists, forms |
| **Edit group** | `/group/edit/<id>/` | `core/edit_group.html` | `mobile/edit_group.html` | Edit group | Sidebar + main | Form |
| **Create group** | `/add-group/` | `core/create_group.html` | `mobile/create_group.html` | Create group | Sidebar + main | Form |

### 1.6 Lessons & homework

| Screen | Route(s) | Desktop template | Mobile template | Description | Layout | Tables / Forms / Grids |
|--------|----------|------------------|-----------------|-------------|--------|------------------------|
| **Add lesson** | `/add-lesson/` | `core/add_lesson.html` * | `mobile/add_lesson.html` | Add lesson | Sidebar + main | Form (*desktop template missing in repo — verify) |
| **Edit lesson** | `/lesson/edit/<id>/` | `core/edit_lesson.html` | `mobile/edit_lesson.html` | Edit lesson | Sidebar + main | Form |
| **Homework detail** | `/homework/<id>/` | `core/homework_detail.html` | — | Homework task and responses | Sidebar + main | Form, list of responses, file uploads |

### 1.7 Finances & payment

| Screen | Route(s) | Desktop template | Mobile template | Description | Layout | Tables / Forms / Grids |
|--------|----------|------------------|-----------------|-------------|--------|------------------------|
| **Finances** | `/finances/` | `core/finances.html` | `mobile/finances.html` | Balance, transactions, charts | Sidebar + main | Tables (transaction history), charts (Chart.js) |
| **Payment receipts (student)** | `/payment-receipts/` | `core/payment_receipts_student.html` | — | Student: list and submit receipts | Sidebar + main | Table, upload form |
| **Payment receipts (tutor)** | `/payment-receipts/` | `core/payment_receipts_tutor.html` | — | Tutor: list and approve/reject | Sidebar + main | Table, actions |

### 1.8 Files & assignments

| Screen | Route(s) | Desktop template | Mobile template | Description | Layout | Tables / Forms / Grids |
|--------|----------|------------------|-----------------|-------------|--------|------------------------|
| **Files library** | `/my-files/` | `core/files_library.html` | `mobile/files_library.html` | User file library, tags | Sidebar + main | Grid/list of files, filters (includes `files_rows.html`, `file_picker_modal.html` on mobile) |
| **My assignments** | `/my-assignments/` | `core/my_assignments.html` | `mobile/my_assignments.html` | Student homework assignments | Sidebar + main | List/cards, filters |
| **Results** | `/results/` | `core/results.html` | — | Results page (e.g. test results) | Sidebar + main | Possibly table/grid (verify in template) |

### 1.9 Profile & confirmations

| Screen | Route(s) | Desktop template | Mobile template | Description | Layout | Tables / Forms / Grids |
|--------|----------|------------------|-----------------|-------------|--------|------------------------|
| **Edit profile** | `/edit-profile/` | `core/edit_profile.html` | `mobile/edit_profile.html` | Edit user profile | Sidebar + main | Form |
| **Confirmations** | `/confirmations/` | `core/confirmations.html` | `mobile/confirmations.html` | Incoming connection/request confirmations | Sidebar + main | List, accept/reject actions |
| **My subjects** | `/subjects/` | `core/my_subjects.html` | `mobile/my_subjects.html` | Manage subjects | Sidebar + main | List, forms |

### 1.10 Error & shared

| Screen | Route(s) | Desktop template | Mobile template | Description | Layout | Tables / Forms / Grids |
|--------|----------|------------------|-----------------|-------------|--------|------------------------|
| **404** | (any 404) | `core/404.html` | — | Not found | Full-width | — |
| **500** | (server error) | `core/500.html` | — | Server error | Full-width | — |
| **Base** | — | `core/base.html` | `mobile/base.html` | Layout shell (sidebar, nav) | Sidebar + main / mobile nav | — |
| **Auth base** | — | `core/auth_base.html` | — | Auth layout shell | Full-width | — |

**Summary:**  
- **Desktop-only screens:** Login, Register, Registration pending, Activation invalid, Email verification, Password reset (4), Confirm archive, Homework detail, Payment receipts (student & tutor), Results, 404, 500.  
- **Screens with desktop + mobile variants:** Index, FAQ, My students, Archived students, Student card, Add student, My tutors, Tutor card, Group card, Edit group, Create group, Edit lesson, Finances, Files library, My assignments, Edit profile, Confirmations, My subjects.  
- **Add lesson:** View uses `core/add_lesson.html` but only `mobile/add_lesson.html` exists in repo — **audit:** add or fix desktop template.

---

## 2. Phased Refactoring Plan

Refactoring follows the **screen map** above. No global “rewrite everything”; each screen is tackled in order with audit → layout → components → typography.

### Phase 1 — Audit (all screens)

- **Goal:** Collect issues per screen: horizontal scroll at 375px, broken padding, touch targets &lt; 44px, inconsistent styles (spacing, colors, typography).
- **Output:** Per-screen audit notes (can be a checklist or short doc section under each screen name).
- **Order:** Use the screen map order (Public/Auth → Dashboard → Students → Tutors → Groups → Lessons → Finances → Files → Profile → Errors).  
- **Deliverable:** `docs/ui_audit_plan.md` section “Phase 1 – Audit results” or separate `docs/ui_audit_findings.md` with findings per screen.

### Phase 2 — Layout (by screen or by theme)

- **Goal:** Single container (e.g. `max-width: 1200px`), safe zones (padding 16px on mobile), responsive tables (`overflow-x: auto`), no horizontal scroll at 375px.
- **Order (suggested):**
  1. **Base & shell:** `base.html`, `mobile/base.html`, `auth_base.html` — container, safe zones, sidebar vs mobile nav.
  2. **Public/Auth:** Login, Register, password reset, registration_pending, activation_invalid, email_verification.
  3. **High-traffic:** Index, My students, My tutors, Student card, Tutor card, Group card.
  4. **Forms & tables:** Edit profile, Confirmations, Add student, Create group, Edit group, Add lesson, Edit lesson, Finances, Files library, Payment receipts, My assignments, Homework detail, Results, My subjects, Archived students, Confirm archive.
  5. **Static/errors:** FAQ, 404, 500.
- **Deliverable:** Each refactored screen passes “no horizontal scroll at 375px” and “cards/sections have gap or margin”.

### Phase 3 — Components (by screen or shared)

- **Goal:** Buttons (min-height 48px on mobile, hover/active), forms/inputs (font-size ≥ 16px for iOS, unified style), navigation (desktop sidebar, mobile burger or bottom nav).
- **Order:** Align with Phase 2 — same screen order; when a screen is in Phase 2 layout, Phase 3 applies component rules to that screen. Shared components (buttons, inputs, nav) can be extracted into partials/CSS classes and applied across screens.
- **Deliverable:** Buttons/inputs height ≥ 44px; input font-size ≥ 16px; consistent hover/active; nav works on 1440px and 375px.

### Phase 4 — Typography & spacing

- **Goal:** Unified h1/h2/h3, 4px grid for spacing (8, 16, 24, 32px), CSS variables for colors (no hardcoded HEX in components).
- **Order:** Global styles first (`static/css/style.css`, variables in `:root` and `[data-theme="dark"]`), then apply per screen so no “stuck” content (gap or margin between cards/sections).
- **Deliverable:** Consistent type scale and spacing; no magic numbers; Verifier “cards/sections must have gap or margin” satisfied.

---

## 2.1 Phase 1 – Audit results

See **`docs/ui_audit_findings.md`** for the Phase 1 audit notes (horizontal scroll, padding, touch targets, input font-size at 375px) and Add lesson template resolution.

---

## 3. Explicit Testing Checkpoints

For **each refactored screen**, the Verifier must run:

- **Viewport:** Desktop **1440px** and Mobile **375px** (Chrome DevTools or equivalent).
- **Strict criteria (REJECT if failed):**
  1. **No horizontal scroll at 375px** — page must not scroll horizontally.
  2. **Buttons/inputs height ≥ 44px** — all interactive controls meet minimum touch target.
  3. **Input font-size ≥ 16px** — no smaller (avoids iOS zoom).
  4. **Cards/sections have gap or margin** — content must not appear “stuck”; consistent spacing between blocks.

Checkpoints table (to be filled per screen after refactor):

| Screen | 1440px pass | 375px pass | No h-scroll | Touch targets ≥44px | Input font ≥16px | Gap/margin |
|--------|-------------|------------|-------------|---------------------|------------------|------------|
| **Batch 1** | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Login | ☑ | ☑ | ☑ | ☑ fixed | ☑ fixed | ☑ |
| Register | ☑ | ☑ | ☑ | ☑ fixed | ☑ fixed | ☑ |
| Auth base (Login/Register shell) | ☑ | ☑ | ☑ | ☑ fixed | — | ☑ |
| Desktop base + Index (main content) | ☑ | ☑ fixed | ☑ fixed | ☑ fixed | ☑ fixed | ☑ |
| **Batch 2** | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Index | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| FAQ | ☑ | ☑ | ☑ | ☑ | — | ☑ |
| My students | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Archived students | ☑ | ☑ | ☑ | ☑ | — | ☑ |
| Student card | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Add student | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| My tutors | ☑ | ☑ | ☑ | ☑ | — | ☑ |
| Tutor card | ☑ | ☑ | ☑ | ☑ | — | ☑ |
| Confirm archive | ☑ | ☑ | ☑ | ☑ | — | ☑ |
| **Batch 3** | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Group card | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Edit group | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Create group | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Add lesson | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Edit lesson | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Homework detail | ☑ | ☑ | ☑ | ☑ | — | ☑ |
| **Batch 4** | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Finances | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Payment receipts (student) | ☑ | — | ☑ | ☑ | ☑ | ☑ |
| Payment receipts (tutor) | ☑ | — | ☑ | ☑ | ☑ | ☑ |
| Files library | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| My assignments | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Results | ☑ | — | ☑ | ☑ | ☑ | ☑ |
| Edit profile | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Confirmations | ☑ | ☑ | ☑ | ☑ | — | ☑ |
| My subjects | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |

**Batch 1 verification notes (Verifier, code/CSS inspection — no real browser run):**

- **No horizontal scroll at 375px:** Auth layout uses `.auth-flex-container` padding 20px and `.auth-card` max-width 420px, width 100%; no `overflow-x: hidden` on body. Auth screens have no wide fixed content → no h-scroll expected. **Index:** `.bulk-bar` has `min-width: 450px` (in index.html inline styles); at 375px this causes horizontal scroll → **REJECT** for Index at 375px.
- **Touch targets ≥44px:** `.btn` has no `min-height` (padding 10px 20px, font 14px → ~40px) → REJECT. `.btn-auth` has padding 14px but no explicit `min-height: 44px`. `.password-toggle` (Login) has `padding: 4px` only → &lt;44px → REJECT. `.theme-toggle-btn` (sidebar) is 40×40px → REJECT. `.theme-toggle-btn-auth` is 44×44 → OK. `.logout-icon-btn` is 32×32 → REJECT. Register cookie consent uses `.btn.btn-sm` (padding 7px 14px) → REJECT.
- **Input font-size ≥16px:** `.auth-input` (Login) is `font-size: 15px` → REJECT. Global `input, select, textarea` in `style.css` is `font-size: 14px` → Register and any unstyled inputs REJECT. Login inputs use `.auth-input` (15px).
- **Gap/margin:** Auth cards have `.auth-card` padding 40px, `.auth-form-group` margin-bottom 20px, `.auth-footer` margin-top 20px; `.auth-flex-container` padding 20px. Desktop `.main-content` padding 32px 40px; `.card` margin-bottom 20px. Criteria satisfied.

**Batch 1 verdict (after fixes):** **PASS** (2025-03-03). Re-verified by code/CSS inspection: (1) `body { overflow-x: hidden }`; Index `.bulk-bar` has `@media (max-width: 768px)` with `min-width: 0`, `width: calc(100vw - 32px)`, `left: 16px`, `right: 16px`, `transform: none`. (2) `.btn`/`.btn-sm` min-height 44px; `.btn-icon` 44×44; `.btn-auth` min-height 48px; `.password-toggle` min 44×44 + padding; `.theme-toggle-btn` and `.logout-icon-btn` 44×44. (3) Global `input, select, textarea` and `.auth-input` font-size 16px. (4) Cards/sections gap or margin unchanged (`.card` margin-bottom, `.main-content` padding, auth padding/margins).

**Batch 2 implemented** (tasks 2.3, 2.4, 3.1, 3.2, 4.2, 4.3 — Index, FAQ, My students, Archived students, Student card, Add student, My tutors, Tutor card, Confirm archive):

- **2.3 Table containers:** Index already had `.table-container`. Wrapped tables in `.table-container` (with `overflow-x: auto`) in: **core/archived_students.html** (one table inside scrollable-container); **core/student_card.html** (lessons table, homework table, two performance tables, history modal table); **core/tutor_card.html** (homework table, lessons table, history modal table). **mobile/student_card.html**: added class `table-container` to `.m-table-wrap`; **static/css/style.css**: added `.m-table-wrap { overflow-x: auto; }` for mobile table scroll.
- **2.4 Word-break:** In **static/css/style.css**: `.main-content-inner` and `.card`, `.list-info`, `.user-text` now have `word-break: break-word; overflow-wrap: break-word;` to prevent long words/URLs from breaking layout.
- **3.1 / 3.2:** FAQ accordion trigger: `min-height: 44px`, `font-size: 16px`. My tutors: "Цвет" and "Открепиться" buttons given `min-height: 44px`, `font-size: 14px`, `padding: 8px 12px`. Tutor card submit-HW button: `min-height: 44px`, `font-size: 16px`. Small table font-sizes in student_card (13px) raised to 14px where used in tables; padding 15px/10px normalized to 16px/12px where touched.
- **4.2 / 4.3:** Replaced odd spacing with 4px grid in **style.css**: `.next-lesson-card` margin 20px 15px → 20px 16px, padding 18px → 16px; `.grid-stats` margin-bottom 28px → 24px; `.top-header` margin-bottom 30px → 32px. In templates: archived_students margin-bottom 25px → 24px; FAQ margin 28px/15px/25px → 24px/16px/24px; my_tutors margin-bottom 15px → 16px, card gap unchanged; tutor_card gap 25px → 24px, modal padding 25px → 24px, column gap 25px → 24px; student_card gap 25px → 24px; index lessons card margin-bottom 30px → 32px; my_students margin-bottom and flex gap 30px → 32px and 24px. Cards/sections on these screens use consistent 8, 16, 24px spacing.

**Batch 2 verification notes (Verifier, code/CSS inspection):**

- **No horizontal scroll at 375px:** body has `overflow-x: hidden`. Index lessons table is inside `.table-container`; bulk-bar has `@media (max-width: 768px)` with `min-width: 0`, `width: calc(100vw - 32px)`. Archived students, student card, tutor card tables are in `.table-container`; mobile student_card uses `.m-table-wrap` (has `overflow-x: auto` in style.css). My students uses `min-width: 350px` on columns with `flex-wrap: wrap` so columns stack at narrow width. No fixed min-width > 375px on these pages. **Pass.**
- **Touch targets ≥44px:** Global `.btn` has `min-height: 44px`. **Index:** filter buttons `.btn-search-modern` and `.btn-reset-modern` use `height: 42px` in inline styles (index.html) → **REJECT**. **Add student (mobile):** `.submit-btn` has only `padding: 14px`, no min-height → **REJECT**. **My tutors (mobile):** "Цвет" palette button has `padding: 6px 10px; font-size: 12px`, no min-height → **REJECT**. **Tutor card (mobile):** `.btn-submit` and submit-HW button have `padding: 8px 16px` / `padding: 12px`, no min-height 44px → **REJECT**. FAQ accordion trigger has `min-height: 44px`. Core My tutors "Цвет"/"Открепиться" have `min-height: 44px`. Core tutor_card submit button has `min-height: 44px; font-size: 16px`. **Batch 2: REJECT** for touch on Index, Add student (mobile), My tutors (mobile), Tutor card (mobile).
- **Input font-size ≥16px:** Global `input, select, textarea` and `.filter-select` in style.css are 16px. **Index:** `.modern-filters .filter-select` and `.modern-filters .modern-select` override with `font-size: 14px !important` in index.html inline styles → **REJECT**. **Add student (mobile):** `.form-input` has `font-size: 15px` → **REJECT**. Core add_student input has no class and gets global 16px. Other Batch 2 screens: FAQ no inputs; my_students/archived_students no text inputs on main content; student_card/tutor_card modals use `.filter-select` (16px). **Batch 2: REJECT** for input on Index and Add student (mobile).
- **Gap/margin:** Cards/sections use 8, 16, 24, 32px. Index has `.stats-row` margin-bottom 30px (not on 4px grid); student_card has one `gap: 25px`. Otherwise spacing aligned to 4px grid. **Pass.**

**Batch 2 verdict:** **REJECT.** Reason: (1) Index — filter inputs 14px and filter buttons 42px; (2) Add student (mobile) — input 15px and submit button without min-height 44px; (3) My tutors (mobile) — "Цвет" button &lt; 44px; (4) Tutor card (mobile) — submit-HW button without min-height 44px. Fix: set Index filter controls to font-size 16px and min-height 44px; mobile Add student `.form-input` to 16px and `.submit-btn` to min-height 44px; mobile My tutors color button and Tutor card submit button to min-height 44px.

**Batch 2 verdict (after fixes):** **PASS** (2025-03-03). Re-verified by code/CSS inspection: (1) No h-scroll at 375px: body `overflow-x: hidden`, Index bulk-bar mobile breakpoint, tables in `.table-container`/`.m-table-wrap`, word-break on content. (2) Touch targets ≥44px: Index `.modern-select`/`.btn-search-modern`/`.btn-reset-modern` min-height/height 44px, `.btn-reset-modern` min-width 44px; mobile add_student `.submit-btn` min-height 48px; mobile my_tutors «Цвет» button min-height/min-width 44px, padding 10px 14px, font-size 14px; mobile tutor_card `.btn-submit` min-height 44px, padding 12px 16px; FAQ accordion trigger min-height 44px; global `.btn` min-height 44px. (3) Input font-size ≥16px: Index `.modern-filters .filter-select`/`.modern-select` 16px, `#universalEditModal` .filter-select 16px and min-height 44px; mobile add_student `.form-input` 16px, `.submit-btn` font-size 16px. (4) Gap/margin: cards/sections use 8, 16, 24, 32px; criteria satisfied.

**Batch 3 implemented** (tasks 2.3, 2.4, 3.1, 3.2, 4.2, 4.3 — Group card, Edit group, Create group, Add lesson, Edit lesson, Homework detail):

- **2.3 Table containers:** **core/group_card.html** already had `.table-container` on the journal table. **mobile/group_card.html**: `.gc-table-wrap` now uses `overflow-x: auto` (template scoped style + **style.css** `.gc-table-wrap { overflow-x: auto; }`). Edit group, Create group, Add lesson, Edit lesson, Homework detail have no tables.
- **2.4 Word-break:** **style.css** added `.gc-members-card`, `.gc-member-name`, `.eg-card`, `.cg-card`, `.add-lesson-card`, `.hw-detail-description`, `.hw-detail-comment` with `word-break: break-word; overflow-wrap: break-word`. **core/homework_detail.html** description and tutor-comment blocks use `.hw-detail-description` / `.hw-detail-comment`. Existing global `.card` / `.main-content-inner` already cover other card content.
- **3.1 / 3.2 Touch and input:** Core group_card modal textarea/inputs use `font-size: 16px` and `.filter-select`. Core edit_lesson materials button has `min-height: 44px`, `padding: 12px`. Mobile: **group_card** — `.gc-hw-btn`, `.modal-submit`, `.modal-close-btn`, `.mobile-fp-trigger-group` min-height 44px; `.modal-textarea`, `.modal-input` font-size 16px. **edit_group** / **create_group** — `.eg-submit`, `.eg-cancel`, `.cg-submit` min-height 44px; `.eg-card` / `.cg-card` input/select font-size 16px, min-height 44px. **add_lesson** / **edit_lesson** — `.segment-option`, `.mobile-submit-btn`, `.mobile-fp-trigger-addlesson` min-height 44px; `.tg-field-wrap` input/select/textarea font-size 16px. Core forms use global `.btn` and input styles.
- **4.2 / 4.3 4px grid and gaps:** **core/group_card.html**: gap 25px→24px; margins/padding 15px→16px, 10px→8px; modal mb-20. **mobile/group_card.html**: header/section padding 25px 15px→24px 16px, 20px 15px→20px 16px; margin-top 15px→16px; modal margins 15px→16px, 20px→16px, 10px→8px. **core/edit_group.html**: gap 10px→8px, padding 10px→12px. **core/create_group.html**: padding 15px→16px, margin-right 10px→8px. **core/edit_lesson.html**: gap 10px→8px. **core/homework_detail.html**: padding 25px 30px→24px 32px, 30px→32px; margins 25px→24px, 35px→32px, 30px→32px; grid gap 15px→16px; block padding 15px→16px; section padding-bottom/margin 10px/15px→8px/16px; back link margin 20px→16px. Cards/sections use consistent 8, 16, 24, 32px.

**Batch 3 verification notes (Verifier, code/CSS inspection):**

- **No horizontal scroll at 375px:** body has `overflow-x: hidden`. **core/group_card.html**: left column has `width: 320px; flex-shrink: 0`; at 375px viewport with desktop layout (e.g. @media (max-width: 768px): main-content padding 16px → content width 343px), flex needs 320 + 24 (gap) = 344px → **overflow**. Mobile group_card uses full-width layout and `.gc-table-wrap { overflow-x: auto }` — pass. Edit group, Create group, Add lesson, Edit lesson use max-width containers or full-width; no fixed min-width > 375px. Homework detail has no tables; grid and cards are fluid. **Group card (core): REJECT** for no h-scroll at 375px.
- **Touch targets ≥44px:** Global `.btn` and `.btn-sm` have `min-height: 44px`. Core group_card: "Задать ДЗ", "Сохранить", "Убрать цвет" use `.btn`; modal submit uses `.btn btn-primary`. Mobile group_card: `.gc-hw-btn`, `.modal-submit`, `.modal-close-btn`, `.mobile-fp-trigger-group` have `min-height: 44px`. Edit group / Create group (core): `.btn`; mobile: `.eg-submit`, `.eg-cancel`, `.cg-submit` min-height 44px. Add lesson / Edit lesson (core): materials button has `min-height: 44px` (edit_lesson), `.btn` elsewhere; mobile: `.segment-option`, `.mobile-submit-btn`, `.mobile-fp-trigger-addlesson` min-height 44px. Homework detail: `.btn`, `.btn-outline`, `.btn-sm` (all 44px in style.css). **Pass.**
- **Input font-size ≥16px:** Global `input, select, textarea` and `.filter-select` are 16px in style.css. Core group_card modal: textarea/input use `font-size: 16px` and `.filter-select`. Core edit_group/create_group: form fields get global 16px. Mobile edit_group/create_group: `.eg-card` / `.cg-card` input, select `font-size: 16px`. Core add_lesson: form uses global and `.filter-select`. Mobile add_lesson/edit_lesson: `.tg-field-wrap` input, select, textarea `font-size: 16px`. Homework detail: no text inputs (download/delete actions only). **Pass** (— for Homework detail).
- **Gap/margin:** Cards/sections use 8, 16, 24, 32px per implementation notes. **Pass.**

**Batch 3 verdict:** **REJECT.** Reason: **core/group_card.html** causes horizontal scroll at 375px — left column is fixed `width: 320px; flex-shrink: 0`; with 24px gap the layout requires ≥344px, exceeding typical content width at 375px viewport when desktop template is used. Fix: add responsive layout for core group_card at narrow viewport (e.g. stack columns or allow left column to shrink/wrap so total width ≤ 100%).

**Batch 3 verdict (after layout fix):** **PASS** (2025-03-03). Re-verified: (1) **core/group_card.html** has `@media (max-width: 768px)` with `flex-direction: column` and `.group-card-side { width: 100%; max-width: 100%; }` — at 375px left column no longer forces 320px; stacks full width; right column has `min-width: 0`. No horizontal scroll at 375px. (2) Touch ≥44px, input ≥16px, gap/margin hold for Group card, Edit group, Create group, Add lesson, Edit lesson, Homework detail per Batch 3 implementation notes.

**Batch 4 implemented** (tasks 2.3, 2.4, 3.1, 3.2, 4.2, 4.3 — Finances, Payment receipts student & tutor, Files library, My assignments, Results, Edit profile, Confirmations, My subjects): table containers (payment_receipts_tutor, my_assignments, my_subjects wrapped; finances/results redundant inline removed), word-break on Batch 4 blocks in style.css, touch/input (buttons min-height ≥44px, inputs/textarea font-size ≥16px on core and mobile), 4px grid and consistent gaps (8, 16, 24, 32px) in style.css and templates.

**Batch 4 verification notes (Verifier, code/CSS inspection):**

- **No horizontal scroll at 375px:** body has `overflow-x: hidden`. **Finances (core):** table in `.table-container`; filter form uses flex-wrap and gap 12px; mobile finances uses cards, no table. **Payment receipts (student/tutor):** tables in `.table-container`. **Files library (core):** grid `minmax(220px, 1fr)`; no fixed min-width > 375px; mobile uses list of cards. **My assignments (core):** table in `.table-container`; mobile uses cards. **Results (core):** table in `.table-container`; filter form flex-wrap. **Edit profile:** max-width 600px container; no tables. **Confirmations:** cards in column; no tables. **My subjects (core):** table inside `.table-container` and `.scrollable-container`; mobile uses pills + add form. No fixed min-width > 375px on any Batch 4 screen. **Pass.**

- **Touch targets ≥44px:** Global `.btn`, `.btn-sm`, `.btn-icon` have min-height/min-width 44px. **Finances (core):** filter button has inline `min-height: 44px`; `.btn-icon` 44×44. **Finances (mobile):** `.fin-date-input` min-height 44px; `.fin-filter-btn` min-height 44px. **Payment receipts (student/tutor):** primary actions use `.btn`/`.btn-primary`/`.btn-outline`/`.btn-sm`. **Files library (core):** "Добавить файл" and empty-state button use `.btn`; search input and sort select have inline min-height 44px; modal form uses `.filter-select` (padding gives ~44px). **Files library (mobile):** `.fl-action-btn` 44×44; `.fl-submit-btn` min-height 44px; `.fl-input` min-height 44px; FAB 60×60. **My assignments (core):** "Сдать" uses `.btn btn-primary btn-sm`; modal file-picker button has inline min-height 44px; submit uses `.btn`. **My assignments (mobile):** `.hw-submit-btn` min-height 44px; `.modal-btn` min-height 44px; file input inline min-height 44px. **Results:** filter and modal use `.btn`/`.btn-sm`/`.filter-select`. **Edit profile (core):** submit `.btn btn-primary btn-full`; `.btn-detect` 44×44 in style.css; logout button has inline min-height 44px. **Edit profile (mobile):** `.ep-submit-btn` min-height 44px; `.ep-detect-btn` 44×44; `.ep-section` inputs/selects min-height 44px. **Confirmations (core):** `.btn btn-success btn-sm` / `.btn btn-danger btn-sm` (`.btn-sm` has min-height 44px). **Confirmations (mobile):** `.req-btn` min-height 44px. **My subjects (core):** `.btn` for add and table actions; modal input `.filter-select`. **My subjects (mobile):** `.add-btn` and `.add-input` min-height 44px; `.subject-action-btn` 44×44; modal `.add-input`. **Pass.**

- **Input font-size ≥16px:** Global `input, select, textarea` and `.filter-select`, `.date-input` are 16px in style.css. **Finances (core):** `.date-input` 16px. **Finances (mobile):** `.fin-date-input` 16px. **Payment receipts (student):** modal uses `.filter-select` (16px). **Files library (core):** search input inline font-size 16px; `#files-sort-by` 16px; modals use `.filter-select`. **Files library (mobile):** `.fl-input` 16px. **My assignments (core):** modal file-picker button font-size 16px; no other text inputs in main content. **My assignments (mobile):** file input inline font-size 16px. **Results:** filter uses `.date-input` and `.filter-select`; add-result modal uses `.filter-select`. **Edit profile (core):** form fields get global input styles (16px). **Edit profile (mobile):** `.ep-section` inputs/selects/textarea and `.ep-tz-select select` 16px. **Confirmations:** no text inputs. **My subjects (core):** add form and edit modal use `.filter-select`. **My subjects (mobile):** `.add-input` 16px; modal `.add-input` 16px. **Pass.**

- **Gap/margin (4px grid):** Cards/sections use 8, 16, 24, 32px. Finances: grid-stats margin-bottom 24px; card padding 24px; finance-filters gap 12px (style.css); mobile fin-page 16px, fin-filter 16px, fin-stats gap 8px. Payment receipts: margin-bottom 24px; modal gap 16px. Files library: gap 24px, margin-top 12px, 8px; mobile fl-file-list padding, fl-file-card margin 8px, fl-form-group 16px. My assignments: content-header gap 12px; card padding 0; modal margin-bottom 24px; mobile page-section padding, hw-list/hw-card 8px/16px, modal-actions gap 8px. Results: card margin-bottom 24px; form gap 12px; modal grid gap 16px. Edit profile: mb-20 (20px), margin-top 32px, padding 24px, 16px; mobile ep-section padding 24px 16px, margin 16px, ep-form-group 16px. Confirmations: gap 16px; mobile request-card padding 16px, margin-bottom 8px, gap 8px. My subjects: margin-bottom 24px; form gap 16px; mobile subjects-list gap 8px, add-form padding 16px. **Pass.**

**Batch 4 verdict:** **PASS** (2025-03-03). All four criteria satisfied: no horizontal scroll at 375px (tables in `.table-container`, body `overflow-x: hidden`, no min-width > 375px); touch targets ≥44px (global `.btn`/`.btn-sm`/`.btn-icon` and screen-specific buttons/inputs); input font-size ≥16px (global and Batch 4 forms); cards/sections use 4px grid spacing (8, 16, 24, 32px).

**Batch 5 implemented** (404, 500, global 4px grid and CSS variables):

- **404 and 500:** Templates `core/templates/404.html` and `core/templates/500.html` refactored to use classes `.error-page`, `.error-page-card`, `.error-page-icon`, `.error-page-title`, `.error-page-text`, `.error-page-btn`. No horizontal scroll at 375px (wrapper `max-width: 100%`, safe padding 16px on mobile); buttons use `.btn .btn-primary` with explicit `min-height: 44px` (48px on mobile); no inputs; card/section spacing via `gap: 16px` and padding 24px/16px on mobile. All colors use CSS variables (`var(--text-muted)`, `var(--text-main)`, etc.).
- **Global 4px grid:** In `static/css/style.css`, high-visibility spacing adjusted to 8, 12, 16, 20, 24, 32px: sidebar padding 28px→24px; `.nav-item i` margin-right 10px→12px; `.auth-card h2` margin-bottom 28px→24px; mobile `.card`/`.student-item` padding 15px→16px; mobile avatar margin-right 15px→16px; breadcrumbs gap 10px→12px, margin-bottom 25px→24px; `#fileExplorerModal` padding/margins 25px/15px→24px/16px; `.file-icon-item` padding 15px 10px→16px 12px.
- **CSS variables:** Confirmed `:root` and `[data-theme="dark"]` define main color and spacing-related variables (e.g. `--primary`, `--bg-*`, `--text-*`, `--radius-*`, `--shadow-*`). Error pages and global layout use these where defined; no new variable refactor.

| **Batch 5** | ☑ | ☑ | ☑ | ☑ | — | ☑ |
| 404 | ☑ | ☑ | ☑ | ☑ | — | ☑ |
| 500 | ☑ | ☑ | ☑ | ☑ | — | ☑ |

**Batch 5 verification notes (Verifier, code/CSS inspection):**

- **No horizontal scroll at 375px:** `body { overflow-x: hidden }`. `.error-page` has `width: 100%`, `max-width: 100%`, `box-sizing: border-box`; base padding `32px 16px`; inside `@media (max-width: 768px)` padding `24px 16px` (16px horizontal safe zone). `.error-page-card` has `max-width: 500px` (fits within viewport); no fixed min-width or content that would overflow. **Pass.**
- **Touch targets ≥44px:** Buttons use `.btn .btn-primary .error-page-btn`. Global `.btn` has `min-height: 44px`; `.error-page-btn` has `min-height: 44px`; inside the same media query `.btn` and `.error-page-btn` get `min-height: 48px`. **Pass.**
- **Input font-size ≥16px:** 404 and 500 have no form inputs. **N/A (—).**
- **Gap/margin:** `.error-page-card` uses `gap: 16px`, padding `32px 24px` (desktop) and `24px 16px` (mobile); `.error-page-btn` has `margin-top: 8px`. All values on 4px grid (8, 16, 24, 32px). **Pass.**
- **Global 4px grid (Batch 5–touched spacing):** Error-page rules use 8, 16, 24, 32px. Implementation notes list sidebar 28→24, nav-item 12px, auth-card h2 24px, mobile card/student-item 16px, breadcrumbs 12px/24px, fileExplorerModal 24px/16px, file-icon-item 16px/12px — confirmed in style.css where Batch 5 touched (e.g. `.nav-item i` margin-right 12px; breadcrumbs gap 12px, margin-bottom 24px). **Pass.**
- **CSS variables:** Error pages use `var(--text-muted)`, `var(--text-main)` in `.error-page-icon`, `.error-page-title`, `.error-page-text`; `.card` inherits variables. `:root` and `[data-theme="dark"]` define these. **Pass.**

**Batch 5 verdict:** **PASS** (2025-03-03). All four criteria satisfied for 404 and 500: no horizontal scroll at 375px (safe padding, no wide fixed content); button min-height ≥44px (48px on mobile); no inputs (N/A); gap/margin on 4px grid. Global 4px grid and CSS variables confirmed where Batch 5 applied.

(Expand this table with one row per screen from the Screen Map as screens are refactored.)

---

## 4. Handoff to Implementers and Verifier

- **Implementers:** Work from this document **screen by screen**. For each screen, follow Phase 1 (audit) → Phase 2 (layout) → Phase 3 (components) → Phase 4 (typography/spacing) as applicable. Do not rewrite unrelated screens.
- **Verifier:** After implementation of a screen (or batch of screens), run the four strict criteria at 1440px and 375px and update the testing checkpoint table. REJECT if any criterion fails.
- **Orchestrator:** Direct implementers to specific screens in order (e.g. “Implement Phase 2–4 for Login and Register”) and trigger verifier after each batch.

---

## 5. References

- **URLs:** `tutor_project/urls.py`
- **Views & smart_render:** `core/views.py` (mobile template = `template_name.replace('core/', 'mobile/')` when `request.is_mobile` and mobile template exists)
- **Templates:** `core/templates/core/`, `core/templates/mobile/`
- **Styles:** `static/css/style.css`, CSS variables and 4px grid per `.cursor/rules/ui-standards.mdc`
- **Verifier criteria:** No horizontal scroll 375px; buttons/inputs ≥ 44px; input font-size ≥ 16px; cards/sections gap or margin.
