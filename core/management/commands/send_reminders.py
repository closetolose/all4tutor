import pytz
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Lessons
from core.utils import send_telegram_notification


class Command(BaseCommand):
    help = 'Отправляет уведомления об уроках за 1 час'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        one_hour_later = now + timedelta(hours=1)

        self.stdout.write(f"[*] Проверка уроков... Сейчас на сервере: {now.strftime('%H:%M:%S')}")
        self.stdout.write(f"[*] Ищем уроки в интервале до: {one_hour_later.strftime('%H:%M:%S')}")

        upcoming_lessons = Lessons.objects.filter(
            start_time__gte=now,
            start_time__lte=one_hour_later,
            reminder_sent=False
        )

        if not upcoming_lessons.exists():
            self.stdout.write(self.style.WARNING("[!] Подходящих уроков не найдено."))
            return

        for lesson in upcoming_lessons:
            user_tz_name = lesson.student.timezone if lesson.student else 'Europe/Moscow'
            try:
                user_tz = pytz.timezone(user_tz_name)
            except pytz.UnknownTimeZoneError:
                user_tz = pytz.UTC
            localized_time = lesson.start_time.astimezone(user_tz)
            formatted_time = localized_time.strftime('%H:%M')
            tutor_name = f"{lesson.tutor.first_name} {lesson.tutor.last_name}"
            location_info = lesson.location if lesson.location else "Не указано"
            # Если в location лежит ссылка, её можно оформить как гиперссылку (в HTML режиме бота)
            if location_info.startswith('http'):
                location_display = f'<a href="{location_info}">Перейти к уроку</a>'
            else:
                location_display = location_info

            subject_name = lesson.subject.name
            msg = (
                f"🔔 <b>Напоминание о занятии</b>\n\n"
                f"👤 <b>Репетитор:</b> {lesson.tutor.first_name} {lesson.tutor.last_name}\n"
                f"📚 <b>Предмет:</b> {lesson.subject.name}\n"
                f"⏰ <b>Начало:</b> {formatted_time} (по вашему времени)\n"
                f"📍 <b>Место:</b> {location_display}"
            )

            # Отправка
            sent_to_student = False
            sent_to_tutor = False

            if lesson.student and lesson.student.telegram_id:
                sent_to_student = send_telegram_notification(lesson.student, msg)
            if lesson.tutor and lesson.tutor.telegram_id:
                sent_to_tutor = send_telegram_notification(lesson.tutor, msg)

            lesson.reminder_sent = True
            lesson.save()

            self.stdout.write(self.style.SUCCESS(
                f"[V] Уведомление по уроку ID {lesson.id} отправлено (Студент: {sent_to_student}, Тичер: {sent_to_tutor})"))