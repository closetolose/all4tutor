from django.db import connection

def wipe():
    print("🧨 Начинаем полную зачистку таблиц...")
    with connection.cursor() as cursor:
        # Отключаем проверку внешних ключей, чтобы MySQL позволил всё удалить
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            print(f"🗑️ Удалена таблица: {table_name}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("✨ База пуста. Теперь можно мигрировать!")

if __name__ == "__main__":
    wipe()