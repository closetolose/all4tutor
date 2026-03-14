from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from core.models import Homework
from core.utils import notify_user


class Command(BaseCommand):
    help = 'Находит просроченные ДЗ, создаёт уведомления ученикам, помечает is_overdue_notified'

    def handle(self, *args, **options):
        now = timezone.now()

        overdue_homeworks = Homework.objects.filter(
            deadline__lt=now,
            deadline__isnull=False,
            is_overdue_notified=False,
        ).exclude(
            status__in=['completed', 'submitted'],
        ).select_related('student', 'subject')

        if not overdue_homeworks.exists():
            self.stdout.write(self.style.WARNING('[!] Просроченных ДЗ без уведомлений не найдено.'))
            return

        count = 0
        for hw in overdue_homeworks:
            try:
                with transaction.atomic():
                    hw.status = 'overdue'
                    hw.is_overdue_notified = True
                    hw.save(update_fields=['status', 'is_overdue_notified', 'updated_at'])

                    link = reverse('homework_detail', args=[hw.id])
                    message = f'Домашнее задание по {hw.subject.name} просрочено. Сдайте работу как можно скорее.'

                    notify_user(
                        hw.student.user,
                        message,
                        link=link,
                        notification_type='warning',
                    )
                    count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'[V] ДЗ ID {hw.id} ({hw.subject.name}) — уведомление создано')
                    )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'[X] Ошибка для ДЗ ID {hw.id}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'[V] Обработано уведомлений: {count}'))
