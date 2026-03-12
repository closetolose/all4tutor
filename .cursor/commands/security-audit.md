# Security Audit

## Overview
Comprehensive security review to identify and fix vulnerabilities in the codebase. Полный отчёт: `SECURITY_AUDIT.md`.

## How to run dependency audit

```bash
docker compose run --rm web sh -c "pip install pip-audit -q && pip-audit"
```

После исправлений обновить `requirements.txt` и при необходимости Dockerfile (upgrade pip/wheel).

## Steps
1. **Dependency audit**
   - Run `pip-audit` (see above)
   - Update vulnerable packages in requirements.txt
   - Re-run audit to confirm

2. **Code security review**
   - No hardcoded secrets (env only)
   - Authentication: login_required on sensitive views
   - Authorization: get_object_or_404(..., tutor=request.user.profile) or student
   - Open redirect: safe_referer_redirect with url_has_allowed_host_and_scheme
   - File uploads: validate type/size (validators.py); receipt file validated in submit_receipt
   - File download: path from DB, ownership checked
   - XSS: escapejs / escapeHtml in templates

3. **Infrastructure security**
   - SECRET_KEY, DB, TELEGRAM from env; .env in .gitignore
   - ALLOWED_HOSTS set; HTTPS and secure cookies when DEBUG=False (see settings.py)

## Security Checklist
- [x] Dependencies: pip-audit run; Pillow 12.1.1; pip/wheel upgraded in Dockerfile
- [x] No hardcoded secrets (env only)
- [x] Input validation (files, receipt, mass-edit student/group)
- [x] Authentication (login_required)
- [x] Authorization (ownership checks, get_tutor_file_ids)
- [x] Open redirect mitigated (safe_referer_redirect)
- [x] CSRF (Django middleware + tokens)
