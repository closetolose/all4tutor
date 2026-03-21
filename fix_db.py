import os
import django
from django.db import connection

# Настраиваем окружение Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'tutor_project.settings')  # ЗАМЕНИ crm_project на имя папки со своим settings.py
django.setup()


def run_fix():
    print("🚀 Запуск исправления базы данных...")

    # Список таблиц и колонок, которые нам нужны
    # Формат: 'имя_таблицы': [('имя_колонки', 'тип_данных')]
    tasks = {
        'lessons': [
            ('created_at', 'DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)'),
            ('updated_at', 'DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)')
        ],
        'homework': [
            ('created_at', 'DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)'),
            ('updated_at', 'DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)')
        ],
        'student_transactions': [
            ('created_at', 'DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)'),
            ('updated_at', 'DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)')
        ],
        'users': [
            ('session_key', 'VARCHAR(100) NULL'),
            ('timezone', "VARCHAR(50) DEFAULT 'Europe/Moscow'")
        ]
    }

    with connection.cursor() as cursor:
        for table, columns in tasks.items():
            for col_name, col_type in columns:
                try:
                    # Пытаемся добавить колонку
                    query = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type};"
                    cursor.execute(query)
                    print(f"✅ Добавлено: {table}.{col_name}")
                except Exception as e:
                    # Если ошибка 1060 (Duplicate column), значит поле уже есть — это нормально
                    if "1060" in str(e):
                        print(f"ℹ️ Пропущено: {table}.{col_name} (уже существует)")
                    else:
                        print(f"❌ Ошибка в {table}.{col_name}: {e}")

    print("\n✨ База данных синхронизирована с кодом!")


if __name__ == "__main__":
    run_fix()