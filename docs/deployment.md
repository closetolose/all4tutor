# Деплой All4Tutors на сервер

## 1. Требования к серверу

- Linux (Ubuntu 20.04+ или Debian)
- Docker и Docker Compose
- Git
- Доступ по SSH

## 2. Установка Docker (если ещё нет)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Перелогиниться или: newgrp docker
```

## 3. Клонирование проекта

```bash
cd /opt  # или другая директория
sudo git clone https://github.com/ВАШ_РЕПОЗИТОРИЙ/all4tutor.git
cd all4tutor
```

Либо загрузите проект через `scp`/`rsync`:

```bash
rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
  ./all4tutor/ user@server:/opt/all4tutor/
```

## 4. Создание .env на сервере

Файл `.env` **не в репозитории** (в .gitignore). Создайте его вручную:

```bash
cd /opt/all4tutor
nano .env
```

Минимальный набор переменных:

```env
SECRET_KEY=ваш_секретный_ключ_из_локального_.env
ALLOWED_HOSTS=all4tutors.ru,www.all4tutors.ru,81.94.159.252,localhost
DEBUG=False

DB_NAME=all4tutors
DB_USER=root
DB_PASSWORD=ваш_пароль_от_MySQL
DB_HOST=db
DB_PORT=3306

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=ваш_email
EMAIL_HOST_PASSWORD=пароль_приложения

TELEGRAM_BOT_TOKEN=ваш_токен_бота
GIGACHAT_CREDENTIALS=ваш_ключ_gigachat
```

**Важно:** скопируйте значения из локального `.env`, не придумывайте новые (кроме паролей, если меняете).

## 5. Согласование docker-compose с .env

В `docker-compose.yml` для `db` заданы `tutor_db`, `tutor_user`, `tutor_password`. Если в `.env` другие значения (`all4tutors`, `root` и т.д.), нужно привести к одному виду.

**Вариант А:** использовать переменные из `.env`:

```yaml
# В секции db:
environment:
  - MYSQL_DATABASE=${DB_NAME}
  - MYSQL_USER=${DB_USER}
  - MYSQL_ROOT_PASSWORD=${DB_PASSWORD}

# В секции web (environment) уже используются DB_* из env_file
```

**Вариант Б:** оставить `tutor_db`/`tutor_user` в compose и в `.env` указать те же значения.

## 6. Первый запуск

```bash
cd /opt/all4tutor
docker compose build --no-cache
docker compose up -d
```

## 7. Миграции и статика

```bash
# Миграции
docker compose exec web python manage.py migrate

# Сбор статики
docker compose exec web python manage.py collectstatic --noinput

# Создание суперпользователя (если нужно)
docker compose exec web python manage.py createsuperuser
```

## 8. Проверка

- Сайт: `http://IP_СЕРВЕРА` или `http://all4tutors.ru`
- Логи: `docker compose logs -f web`
- Ошибки: `docker compose logs web --tail 100`

## 9. Обновление проекта (после изменений)

```bash
cd /opt/all4tutor
git pull   # или загрузите файлы через rsync

docker compose build web
docker compose up -d web

docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
```

## 10. SSL (HTTPS) с Let's Encrypt

1. Создайте директории:
   ```bash
   mkdir -p nginx/certbot/conf nginx/certbot/www
   ```

2. Временно отключите редирект на HTTPS в `nginx/conf.d/default.conf`.

3. Запустите certbot (через отдельный контейнер или на хосте):
   ```bash
   docker run -it --rm -v $(pwd)/nginx/certbot/conf:/etc/letsencrypt \
     -v $(pwd)/nginx/certbot/www:/var/www/certbot \
     certbot/certbot certonly --webroot -w /var/www/certbot \
     -d all4tutors.ru -d www.all4tutors.ru
   ```

4. Настройте nginx на HTTPS и включите редирект.

## 11. Резервное копирование

**База данных:**
```bash
docker compose exec db mysqldump -u root -p${DB_PASSWORD} all4tutors > backup_$(date +%Y%m%d).sql
```

**Медиафайлы:**
```bash
docker compose exec web tar czf - /app/media > media_backup_$(date +%Y%m%d).tar.gz
```

## 12. Частые проблемы

| Проблема | Решение |
|----------|---------|
| 502 Bad Gateway | Проверить `docker compose logs web`, перезапустить `docker compose restart web` |
| Статика не отдаётся | Выполнить `collectstatic`, проверить volumes nginx |
| GigaChat не работает | Добавить `GIGACHAT_CREDENTIALS` в `.env`, перезапустить web |
| Миграции не применяются | `docker compose exec web python manage.py migrate` |
| .env не подхватывается | Запускать `docker compose` из директории проекта, проверить `env_file: .env` |
