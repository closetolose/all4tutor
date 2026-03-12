# Run All Tests and Fix Failures

## Overview
Execute the full test suite and systematically fix any failures, ensuring code quality and functionality.

## How to run tests

**Docker (с SQLite, без MySQL):**
```bash
docker compose run --rm -e DB_HOST= -e DB_NAME= -e DB_USER= -e DB_PASSWORD= web python manage.py test --verbosity=2
```

**Только приложение core:**
```bash
docker compose run --rm -e DB_HOST= -e DB_NAME= -e DB_USER= -e DB_PASSWORD= web python manage.py test core --verbosity=2
```

Без `DB_HOST` в настройках используется SQLite (тестовая БД создаётся в памяти). С `DB_HOST` (обычный запуск) используется MySQL — для тестов нужны права на создание БД `test_*`.

## Steps
1. **Run test suite**
   - Execute all tests in the project
   - Capture output and identify failures
   - Check both unit and integration tests

2. **Analyze failures**
   - Categorize by type: flaky, broken, new failures
   - Prioritize fixes based on impact
   - Check if failures are related to recent changes

3. **Fix issues systematically**
   - Start with the most critical failures
   - Fix one issue at a time
   - Re-run tests after each fix
