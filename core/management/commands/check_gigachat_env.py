"""
Диагностика: почему GIGACHAT_CREDENTIALS не загружается из .env.
Запуск: python manage.py check_gigachat_env
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Проверка загрузки GIGACHAT_CREDENTIALS из .env и окружения'

    def handle(self, *args, **options):
        base_dir = getattr(settings, 'BASE_DIR', None)
        cwd = os.getcwd()
        this_file = os.path.abspath(__file__)
        # core/management/commands/check_gigachat_env.py -> 4 уровня вверх до корня
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(this_file))))

        self.stdout.write('=== Диагностика GIGACHAT_CREDENTIALS ===\n')

        # 1. Пути
        self.stdout.write(f'BASE_DIR: {base_dir}')
        self.stdout.write(f'os.getcwd(): {cwd}')
        self.stdout.write(f'project_root (от core/): {project_root}\n')

        # 2. Проверка .env
        paths = [
            (os.path.join(str(base_dir), '.env') if base_dir else None, 'BASE_DIR/.env'),
            (os.path.join(project_root, '.env'), 'project_root/.env'),
            (os.path.join(cwd, '.env'), 'cwd/.env'),
        ]
        for path, label in paths:
            if path:
                exists = os.path.isfile(path)
                self.stdout.write(f'{label}: {"ЕСТЬ" if exists else "НЕТ"}')
                if exists:
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as f:
                            for line in f:
                                if line.strip().startswith('GIGACHAT_CREDENTIALS='):
                                    val = line.split('=', 1)[1].strip()[:20] + '...'
                                    self.stdout.write(self.style.SUCCESS(f'  -> Найдено в файле (первые 20 символов): {val}'))
                                    break
                        else:
                            self.stdout.write(self.style.WARNING('  -> Переменная не найдена в файле'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  -> Ошибка чтения: {e}'))
        self.stdout.write('')

        # 3. os.environ
        creds_env = os.environ.get('GIGACHAT_CREDENTIALS')
        if creds_env:
            self.stdout.write(self.style.SUCCESS(f'os.environ["GIGACHAT_CREDENTIALS"]: ЕСТЬ ({len(creds_env)} символов)'))
        else:
            self.stdout.write(self.style.WARNING('os.environ["GIGACHAT_CREDENTIALS"]: НЕТ'))

        # 4. settings
        creds_settings = getattr(settings, 'GIGACHAT_CREDENTIALS', None)
        if creds_settings:
            self.stdout.write(self.style.SUCCESS(f'settings.GIGACHAT_CREDENTIALS: ЕСТЬ ({len(creds_settings)} символов)'))
        else:
            self.stdout.write(self.style.WARNING('settings.GIGACHAT_CREDENTIALS: НЕТ'))

        self.stdout.write('\n=== Итог ===')
        if creds_env or creds_settings:
            self.stdout.write(self.style.SUCCESS('Ключ доступен, бот должен работать.'))
        else:
            self.stdout.write(self.style.ERROR(
                'Ключ НЕ найден. Проверьте:\n'
                '1. .env в корне проекта (рядом с docker-compose.yml)\n'
                '2. Строка: GIGACHAT_CREDENTIALS=ваш_ключ\n'
                '3. При Docker: docker-compose up перезапустите после добавления .env\n'
                '4. При Docker: env_file: .env в docker-compose.yml'
            ))
