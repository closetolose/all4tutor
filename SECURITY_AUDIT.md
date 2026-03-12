# Security Audit Report

**Date:** 2026-02 (updated 2026-03)  
**Scope:** Dependencies, application code, infrastructure.

---

## 1. Dependencies

- **Django 5.2.11** — in use; keep updated to latest 5.2.x for security fixes (e.g. 5.2.9+ for CVE-2025-*).
- **django-environ** — used for env vars (no hardcoded secrets).
- **django-ratelimit** — present in requirements; currently commented out in views (re-enable for login/register when feasible).
- **Pillow** — обновлён до 12.1.1 (CVE-2026-25990). В `requirements.txt`: `pillow==12.1.1`.
- **pip / wheel** — в Dockerfile добавлен `pip install --upgrade pip wheel` перед установкой зависимостей (CVE-2025-8869, CVE-2026-1703, CVE-2026-24049).
- **Recommendation:** Периодически запускать `pip-audit` в контейнере:  
  `docker compose run --rm web sh -c "pip install pip-audit -q && pip-audit"`.

---

## 2. Code Security (Fixes Applied)

### 2.1 Open Redirect (Fixed)

- **Risk:** `redirect(request.META.get('HTTP_REFERER', 'index'))` could send users to an attacker-controlled URL if Referer was forged.
- **Fix:** Introduced `safe_referer_redirect(request, default='index')` using `url_has_allowed_host_and_scheme()` so redirects only go to `ALLOWED_HOSTS`. All previous `redirect(HTTP_REFERER, ...)` calls now use this helper.

### 2.2 File Library IDOR (Fixed)

- **Risk:** When attaching materials to homework (add/edit lesson, mass edit, group homework), `file_ids` from the client were used without checking ownership. A tutor could attach another tutor’s files.
- **Fix:** Added `get_tutor_file_ids(tutor_profile, raw_ids)` that returns only IDs of `FilesLibrary` rows belonging to that tutor. All homework material assignment paths now use this filtered list:
  - `add_homework`
  - `edit_homework` (student card)
  - `bulk_action_lessons` (mass_edit materials)
  - Group homework assignment in `group_card`

### 2.3 Mass Edit Student/Group (Fixed)

- **Risk:** In bulk mass_edit, `new_student` and `new_group` were applied without checks; a tutor could assign lessons to arbitrary student/group IDs.
- **Fix:** Before applying:
  - `new_student` is used only if `ConnectionRequest` exists for this tutor with that student and status in `['confirmed','archived']`.
  - `new_group` is used only if `StudyGroups` has that id and `tutor=request.user.profile`.
  - Invalid IDs are ignored (set to None for that update).

### 2.4 Already in Good Shape

- **student_card / add_homework:** Access to a student is checked via `ConnectionRequest` (confirmed/archived) before showing the card or adding homework.
- **Object access:** Critical views use `get_object_or_404(..., tutor=request.user.profile)` or equivalent (lessons, groups, files, homework, etc.).
- **CSRF:** Django middleware is enabled; forms use `{% csrf_token %}`.
- **Passwords:** Django validators and `validate_password` in registration form; no plaintext storage.
- **XSS:** File names in JS are escaped with `escapeHtml()` where injected into DOM (e.g. file picker chips).

---

## 3. Infrastructure & Config

- **SECRET_KEY:** Loaded from environment only (`env('SECRET_KEY')`); no default in code. Ensure `.env` is not committed and is set in production.
- **DEBUG:** From env (default False in `environ.Env`). Production should set `DEBUG=False`.
- **ALLOWED_HOSTS:** From env list; default includes all4tutors.ru. Set explicitly in production.
- **HTTPS (when DEBUG=False):** `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS, `SECURE_CONTENT_TYPE_NOSNIFF` are set.
- **TELEGRAM_BOT_TOKEN:** From env with `default=None`; optional. Do not commit real token.

---

## 4. Security Checklist

| Item | Status |
|------|--------|
| Dependencies reviewed / updated | Pillow 12.1.1; pip/wheel upgrade in Dockerfile; pip-audit run 2026-03 |
| No hardcoded secrets | Confirmed (env only; .env, secrets.json in .gitignore) |
| Input validation (file IDs, student/group in mass edit; receipt file type/size) | Implemented |
| Authentication (login_required where needed) | In place |
| Authorization (tutor/student ownership checks) | In place; get_object_or_404(..., tutor=request.user.profile) |
| Open redirect | Fixed via safe_referer_redirect + url_has_allowed_host_and_scheme |
| CSRF on state-changing views | Django middleware + {% csrf_token %} |
| HTTPS and secure cookies in production | Set when DEBUG=False |
| File download (FileResponse) | Path from DB, ownership by tutor; no user-controlled path |
| XSS in templates | escapejs / escapeHtml used for user data in JS and DOM |

---

## 5. Optional Next Steps

1. Re-enable `django-ratelimit` for login and registration after ensuring the package is installed in the deployment environment.
2. Добавить в CI запуск `pip-audit` и исправлять найденные уязвимости.
3. Consider rate limiting for sensitive API-style endpoints (e.g. file search) if they become public or high-traffic.
4. Admin URL (`/secretplace/`) — по желанию заменить на случайный путь и не раскрывать в публичных местах.
