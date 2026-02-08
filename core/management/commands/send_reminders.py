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
            msg = f"⏰ <b>Напоминание!</b>\nУрок {lesson.subject.name} начнется в {lesson.start_time.strftime('%H:%M')}"

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