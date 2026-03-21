import os

import pytz
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint
from django.utils import timezone

from .validators import validate_file_size, validate_chat_file, validate_receipt_file
import uuid



class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='profile', db_column="user_id"
    )
    id = models.AutoField(primary_key=True)
    ROLE_CHOICES = [
        ('tutor', 'Репетитор'),
        ('student', 'Ученик'),
    ]
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=7, choices=ROLE_CHOICES)
    address = models.CharField(max_length=255, blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    telegram_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Telegram")
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='UTC',
        verbose_name="Часовой пояс"
    )
    school_class = models.CharField(max_length=20, verbose_name="Класс", blank=True, null=True)
    parent_name = models.CharField(max_length=255, verbose_name="Имя Отчество родителя", blank=True, null=True)
    parent_phone = models.CharField(max_length=20, verbose_name="Контакты родителя", blank=True, null=True)
    session_key = models.CharField(max_length=100, default=uuid.uuid4, editable=False)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class FileTag(models.Model):
    """Тег файлов репетитора (уникальное имя в рамках репетитора)."""
    tutor = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='file_tags')
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'file_tags'
        unique_together = ('tutor', 'name')

    def __str__(self):
        return self.name


class FilesLibrary(models.Model):
    tutor = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='materials')
    file = models.FileField(
        upload_to='tutor_materials/%Y/%m/%d/',
        null=True,
        blank=True,
        validators=[validate_file_size],
    )
    file_name = models.CharField(max_length=30,verbose_name="Название файла")
    upload_date = models.DateTimeField(default=timezone.now,blank=True)
    tags = models.ManyToManyField('FileTag', blank=True, related_name='files')

    class Meta:
        db_table = 'files_library'

    def __str__(self):
        return self.file_name

    def get_extension(self):
        if not self.file:
            return ""
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()


class LessonAttendance(models.Model):
    lesson = models.ForeignKey('Lessons', models.CASCADE, related_name='attendances')
    student = models.ForeignKey('Profile', models.CASCADE)
    is_paid = models.BooleanField(default=False)
    was_present = models.BooleanField(default=False)

    class Meta:
        db_table = 'lesson_attendance'
        unique_together = ('lesson', 'student')


class StudyGroups(models.Model):
    name = models.CharField(max_length=100)
    tutor = models.ForeignKey('Profile', models.CASCADE)
    subject = models.ForeignKey('Subjects', models.CASCADE)
    students = models.ManyToManyField('Profile', related_name='study_groups', blank=True)
    is_archived = models.BooleanField(default=False, verbose_name='В архиве')

    class Meta:
        db_table = 'study_groups'

    def __str__(self):
        return f"Группа: {self.name}"


class Lessons(models.Model):
    tutor = models.ForeignKey('Profile', models.CASCADE)
    subject = models.ForeignKey('Subjects', on_delete=models.PROTECT,related_name='lessons')
    student = models.ForeignKey(
        'Profile', on_delete=models.CASCADE,
        related_name='lessons_student_set', blank=True, null=True
    )
    group = models.ForeignKey(
        StudyGroups, on_delete=models.CASCADE,
        blank=True, null=True, verbose_name="Группа"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Заметки")
    homework = models.TextField(blank=True, null=True, verbose_name="Домашнее задание")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.IntegerField(default=60, verbose_name="Длительность (мин)")
    format = models.CharField(max_length=12)
    location = models.TextField(blank=True, null=True)
    series_id = models.UUIDField(default=None, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    materials = models.ManyToManyField('FilesLibrary', blank=True, related_name='lessons_materials')
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now,blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lessons'
        constraints = [
            CheckConstraint(check=models.Q(price__gte=0), name='lessons_price_non_negative'),
            CheckConstraint(check=models.Q(duration__gt=0), name='lessons_duration_positive'),
        ]
        indexes = [
            models.Index(fields=['tutor', 'start_time'], name='lessons_tutor_start'),
            models.Index(fields=['student', 'start_time'], name='lessons_student_start'),
        ]

    def save(self, *args, **kwargs):
        # end_time является производным полем: считается из start_time и duration.
        # Это устраняет аномалии обновления, если где-то забудут пересчитать end_time.
        if self.start_time is not None and self.duration is not None:
            self.end_time = self.start_time + timedelta(minutes=int(self.duration))
        return super().save(*args, **kwargs)

    @property
    def is_paid(self):
        """Вычисляется из LessonAttendance: оплачено, если все присутствовавшие оплачены."""
        present = self.attendances.filter(was_present=True)
        if not present.exists():
            return False
        return not present.filter(is_paid=False).exists()


class Subjects(models.Model):
    name = models.CharField(max_length=100)
    tutor = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='subjects')

    class Meta:
        db_table = 'subjects'
        unique_together = ('name', 'tutor')

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TYPES = [('deposit', 'Пополнение'), ('withdrawal', 'Списание')]
    student = models.ForeignKey('Profile', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    tutor = models.ForeignKey('Profile', on_delete=models.SET_NULL, null=True, blank=True)
    attendance = models.ForeignKey('LessonAttendance', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPES)
    description = models.CharField(max_length=255, blank=True, default='')
    date = models.DateTimeField(default=timezone.now,blank=True)

    class Meta:
        db_table = 'student_transactions'
        ordering = ['-date']
        constraints = [
            CheckConstraint(check=models.Q(amount__gt=0), name='transaction_amount_positive'),
        ]


class PaymentReceipt(models.Model):
    """Чек об оплате: ученик загружает, репетитор подтверждает или отклоняет."""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('approved', 'Подтверждён'),
        ('rejected', 'Отклонён'),
    ]
    student = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_receipts')
    tutor = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_receipts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_date = models.DateField()
    file = models.FileField(upload_to='payment_receipts/%Y/%m/', validators=[validate_receipt_file])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payment_receipts'
        ordering = ['-created_at']
        constraints = [
            CheckConstraint(check=models.Q(amount__gt=0), name='payment_receipt_amount_positive'),
        ]


class ConnectionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждено'),
        ('rejected', 'Отклонено'),
        ('archived', 'В архиве'),
    ]

    tutor = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sent_requests')
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now,blank=True)
    color_hex = models.CharField(max_length=7, null=True, blank=True)  # цвет репетитора для ученика (задаёт ученик)
    tutor_color_hex = models.CharField(max_length=7, null=True, blank=True)  # цвет связи для репетитора (задаёт репетитор)
    tutor_note = models.TextField(blank=True, null=True, verbose_name='Заметка репетитора об ученике')
    # Заявка на открепление (ученик → админ)
    unlink_requested = models.BooleanField(default=False, verbose_name='Заявка на открепление')
    unlink_reason = models.TextField(blank=True, null=True, verbose_name='Причина открепления')
    unlink_requested_at = models.DateTimeField(null=True, blank=True)
    unlink_reviewed_at = models.DateTimeField(null=True, blank=True)
    unlink_reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='unlink_reviews'
    )

    class Meta:
        db_table = 'connection_requests'
        indexes = [
            models.Index(fields=['tutor', 'status'], name='conn_req_tutor_status'),
            models.Index(fields=['student', 'status'], name='conn_req_student_status'),
        ]


class UserGroupColor(models.Model):
    """Цветовая метка группы для пользователя (репетитор или ученик)."""
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='group_colors')
    group = models.ForeignKey(StudyGroups, on_delete=models.CASCADE, related_name='user_colors')
    color_hex = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        db_table = 'user_group_colors'
        unique_together = ('user', 'group')


class StudentTariff(models.Model):
    tutor = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='tutor_tariffs')
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(StudyGroups, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            # Ровно одно поле должно быть заполнено: либо индивидуальный тариф для ученика,
            # либо тариф для группы.
            CheckConstraint(
                check=(
                    (models.Q(student__isnull=False, group__isnull=True)) |
                    (models.Q(student__isnull=True, group__isnull=False))
                ),
                name='student_tariff_student_xor_group',
            ),
            # Для индивидуальных тарифов уникальность по (tutor, student, subject).
            # Для групповых строк `student` = NULL, а значит уникальность не конфликтует.
            models.UniqueConstraint(
                fields=('tutor', 'student', 'subject'),
                name='student_tariff_unique_student',
            ),
            # Для групповых тарифов уникальность по (tutor, group, subject).
            # Для индивидуальных строк `group` = NULL.
            models.UniqueConstraint(
                fields=('tutor', 'group', 'subject'),
                name='student_tariff_unique_group',
            ),
            CheckConstraint(check=models.Q(price__gte=0), name='student_tariff_price_non_negative'),
        ]


class Notification(models.Model):
    """In-app уведомление для пользователя (например, о просроченном ДЗ)."""
    TYPE_CHOICES = [
        ('warning', 'Предупреждение'),
        ('info', 'Информация'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='warning')

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read'], name='notif_user_is_read'),
        ]


class GroupHomework(models.Model):
    """Общее ДЗ группы: одно описание, срок и набор файлов для всех учеников."""

    group = models.ForeignKey('StudyGroups', on_delete=models.CASCADE, related_name='homework_assignments')
    description = models.TextField(verbose_name='Описание задания')
    deadline = models.DateTimeField(null=True, blank=True)
    files = models.ManyToManyField('FilesLibrary', blank=True, related_name='group_homework_files')
    created_at = models.DateTimeField(default=timezone.now, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'group_homework'
        ordering = ['-created_at']

    def __str__(self):
        return f'ДЗ группы «{self.group.name}»'


class Homework(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Задано'),
        ('submitted', 'На проверке'),
        ('revision', 'Доработать'),
        ('completed', 'Выполнено'),
        ('overdue', 'Просрочено'),
    ]

    tutor = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='assigned_homework')
    student = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='student_homework')
    subject = models.ForeignKey('Subjects', on_delete=models.CASCADE)
    group_assignment = models.ForeignKey(
        'GroupHomework',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_homeworks',
    )
    description = models.TextField(verbose_name="Описание задания")
    files = models.ManyToManyField('FilesLibrary', blank=True, related_name='homework_files')
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    is_overdue_notified = models.BooleanField(default=False)
    tutor_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий репетитора")
    created_at = models.DateTimeField(default=timezone.now,blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'homework'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status'], name='homework_student_status'),
            models.Index(fields=['tutor', 'deadline'], name='homework_tutor_deadline'),
        ]

    @property
    def effective_description(self):
        if self.group_assignment_id:
            return self.group_assignment.description
        return self.description

    @property
    def effective_deadline(self):
        if self.group_assignment_id:
            return self.group_assignment.deadline
        return self.deadline

    @property
    def effective_files(self):
        if self.group_assignment_id:
            return self.group_assignment.files.all()
        return self.files.all()

    @property
    def has_effective_attachments(self):
        if self.group_assignment_id:
            return self.group_assignment.files.exists()
        return self.files.exists()


class HomeworkResponse(models.Model):
    homework = models.ForeignKey('Homework', on_delete=models.CASCADE, related_name='responses')
    file = models.FileField(
        upload_to='student_responses/',
        validators=[validate_file_size],
    )
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ответ на {self.homework.subject}"


class TestResult(models.Model):
    """Результат проверочной/контрольной работы (модуль Аналитика). Репетитор = subject.tutor."""
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='test_results_as_student')
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE, related_name='test_results')
    max_score = models.DecimalField(max_digits=8, decimal_places=2, help_text='Максимальный балл')
    score = models.DecimalField(max_digits=8, decimal_places=2, help_text='Полученный балл')
    date = models.DateField(default=timezone.now)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'test_results'
        ordering = ['-date']
        constraints = [
            CheckConstraint(check=models.Q(max_score__gt=0), name='test_result_max_score_positive'),
            CheckConstraint(check=models.Q(score__gte=0), name='test_result_score_non_negative'),
            CheckConstraint(check=models.Q(score__lte=models.F('max_score')), name='test_result_score_lte_max'),
        ]

    @property
    def percent(self):
        if self.max_score and self.max_score > 0:
            return round(float(self.score) / float(self.max_score) * 100, 1)
        return None


class ChatMessage(models.Model):
    """Сообщение в чате между репетитором и учеником."""
    connection = models.ForeignKey(
        ConnectionRequest,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    sender = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='sent_chat_messages'
    )
    text = models.TextField(blank=True)
    file = models.FileField(
        upload_to='chat_files/%Y/%m/',
        blank=True,
        null=True,
        validators=[validate_chat_file],
    )
    file_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['connection', 'is_read'], name='chat_conn_is_read'),
        ]

    def is_image(self):
        if not self.file:
            return False
        ext = (self.file_name or self.file.name or '').lower().split('.')[-1]
        return ext in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp')


