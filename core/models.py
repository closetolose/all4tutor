import os

import pytz
from django.conf import settings
from django.db import models
from django.utils import timezone

from .validators import validate_file_size
import uuid



class Users(models.Model):
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


class FilesLibrary(models.Model):
    tutor = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='materials')
    file = models.FileField(
        upload_to='tutor_materials/%Y/%m/%d/',
        null=True,
        blank=True,
        validators=[validate_file_size],
    )
    file_name = models.CharField(max_length=30,verbose_name="Название файла")
    upload_date = models.DateTimeField(default=timezone.now,blank=True)

    class Meta:
        db_table = 'files_library'

    def __str__(self):
        return self.file_name

    def get_extension(self):
        if not self.file:
            return ""
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()


class GroupMembers(models.Model):
    group = models.ForeignKey('StudyGroups', models.CASCADE)
    student = models.ForeignKey('Users', models.CASCADE)

    class Meta:
        db_table = 'group_members'


class LessonAttendance(models.Model):
    lesson = models.ForeignKey('Lessons', models.CASCADE, related_name='attendances')
    student = models.ForeignKey('Users', models.CASCADE)
    is_paid = models.BooleanField(default=False)
    was_present = models.BooleanField(default=False)

    class Meta:
        db_table = 'lesson_attendance'
        unique_together = ('lesson', 'student')


class StudyGroups(models.Model):
    name = models.CharField(max_length=100)
    tutor = models.ForeignKey('Users', models.CASCADE)
    subject = models.ForeignKey('Subjects', models.CASCADE)
    students = models.ManyToManyField('Users', related_name='study_groups', blank=True)

    class Meta:
        db_table = 'study_groups'

    def __str__(self):
        return f"Группа: {self.name}"


class Lessons(models.Model):
    tutor = models.ForeignKey('Users', models.CASCADE)
    subject = models.ForeignKey('Subjects', on_delete=models.PROTECT,related_name='lessons')
    student = models.ForeignKey(
        'Users', on_delete=models.CASCADE,
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
    is_paid = models.BooleanField(default=False)
    series_id = models.UUIDField(default=None, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    materials = models.ManyToManyField('FilesLibrary', blank=True, related_name='lessons_materials')
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now,blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lessons'


class StudentBalance(models.Model):
    tutor = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='student_balances')
    student = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='balances_with_tutors')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('tutor', 'student')

class Subjects(models.Model):
    name = models.CharField(max_length=100)
    tutor = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='subjects')

    class Meta:
        db_table = 'subjects'
        unique_together = ('name', 'tutor')

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TYPES = [('deposit', 'Пополнение'), ('withdrawal', 'Списание')]
    student = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='transactions')
    tutor = models.ForeignKey('Users', on_delete=models.CASCADE)
    attendance = models.ForeignKey('LessonAttendance', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPES)
    description = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(default=timezone.now,blank=True)

    class Meta:
        db_table = 'student_transactions'
        ordering = ['-date']





class TutorSubjects(models.Model):
    tutor = models.ForeignKey('Users', models.CASCADE, db_column='tutor_id')
    subject = models.ForeignKey(Subjects, models.CASCADE, db_column='subject_id')

    class Meta:
        managed = True
        db_table = 'tutor_subjects'
        unique_together = (('tutor', 'subject'),)


class ConnectionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждено'),
        ('rejected', 'Отклонено'),
        ('archived', 'В архиве'),
    ]

    tutor = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='sent_requests')
    student = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now,blank=True)

    class Meta:
        db_table = 'connection_requests'


class StudentTariff(models.Model):
    tutor = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='tutor_tariffs')
    student = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(StudyGroups, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('tutor', 'student', 'subject')


class StudentPerformance(models.Model):
    TYPE_CHOICES = [('hw', 'Домашняя работа'), ('test', 'Контрольная работа')]
    student = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='performance')
    lesson = models.ForeignKey('Lessons', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    score = models.IntegerField(help_text="Оценка или процент выполнения")
    comment = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now,blank=True)


class Homework(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Задано'),
        ('submitted', 'На проверке'),
        ('revision', 'Доработать'),
        ('completed', 'Выполнено'),
    ]

    tutor = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='assigned_homework')
    student = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='student_homework')
    subject = models.ForeignKey('Subjects', on_delete=models.CASCADE)
    description = models.TextField(verbose_name="Описание задания")
    files = models.ManyToManyField('FilesLibrary', blank=True, related_name='homework_files')
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    tutor_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий репетитора")
    created_at = models.DateTimeField(default=timezone.now,blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'homework'
        ordering = ['-created_at']


class HomeworkResponse(models.Model):
    homework = models.ForeignKey('Homework', on_delete=models.CASCADE, related_name='responses')
    file = models.FileField(
        upload_to='student_responses/',
        validators=[validate_file_size],
    )
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now,blank=True)
    student = models.ForeignKey('Users', on_delete=models.CASCADE, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ответ от {self.homework.student} на {self.homework.subject}"


class TutorStudentNote(models.Model):
    tutor = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='notes_created')
    student = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='notes_about_me')
    text = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tutor', 'student')


